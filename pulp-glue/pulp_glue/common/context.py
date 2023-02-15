import datetime
import re
import sys
import time
from typing import Any, ClassVar, Dict, List, Mapping, NamedTuple, Optional, Set, Type, Union

from packaging.version import parse as parse_version
from pulp_glue.common.i18n import get_translation
from pulp_glue.common.openapi import OpenAPI, OpenAPIError, UploadsMap
from requests import HTTPError

translation = get_translation(__name__)
_ = translation.gettext

DEFAULT_LIMIT = 25
BATCH_SIZE = 25
DATETIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ",  # Pulp format
    "%Y-%m-%d",  # intl. format
    "%Y-%m-%d %H:%M:%S",  # ... with time
    "%Y-%m-%dT%H:%M:%S",  # ... with time and T as a separator
    "%y/%m/%d",  # US format
    "%y/%m/%d %h:%M:%S %p",  # ... with time
    "%y/%m/%dT%h:%M:%S %p",  # ... with time and T as a separator
    "%y/%m/%d %H:%M:%S",  # ... with time 24h
    "%y/%m/%dT%H:%M:%S",  # ... with time 24h and T as a separator
    "%x",  # local format
    "%x %X",  # ... with time
    "%xT%X",  # ... with time and T as a separator
]

href_regex = re.compile(r"\/([a-z0-9-_]+\/)+", flags=re.IGNORECASE)


class PreprocessedEntityDefinition(Dict[str, Any]):
    pass


EntityDefinition = Union[Dict[str, Any], PreprocessedEntityDefinition]


class PluginRequirement(NamedTuple):
    name: str
    min: Optional[str] = None
    max: Optional[str] = None
    feature: Optional[str] = None
    inverted: bool = False


class PulpException(Exception):
    pass


class PulpNoWait(Exception):
    pass


def _preprocess_value(value: Any) -> Any:
    if isinstance(value, PulpEntityContext):
        return value.pulp_href
    if isinstance(value, Mapping):
        return {k: _preprocess_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_preprocess_value(item) for item in value]
    return value


def preprocess_payload(payload: EntityDefinition) -> EntityDefinition:
    if isinstance(payload, PreprocessedEntityDefinition):
        return payload

    return PreprocessedEntityDefinition(
        {key: _preprocess_value(value) for key, value in payload.items() if value is not None}
    )


class PulpContext:
    """
    Abstract class for the global PulpContext object.
    It is an abstraction layer for api access and output handling.
    """

    def echo(self, message: str, nl: bool = True, err: bool = False) -> None:
        raise NotImplementedError("PulpContext is an abstract class.")

    def prompt(self, text: str, hide_input: bool = False) -> Any:
        raise NotImplementedError("PulpContext is an abstract class.")

    def __init__(
        self,
        api_root: str,
        api_kwargs: Dict[str, Any],
        format: str,
        background_tasks: bool,
        timeout: int,
    ) -> None:
        self._api: Optional[OpenAPI] = None
        self.api_path: str = api_root + "api/v3/"
        self._api_kwargs = api_kwargs
        self._needed_plugins: List[PluginRequirement] = []
        self.isatty: bool = sys.stdout.isatty()

        self.format: str = format
        self.background_tasks: bool = background_tasks
        self.timeout: int = timeout
        self.start_time: Optional[datetime.datetime] = None

    def _patch_api_spec(self) -> None:
        # A place for last minute fixes to the api_spec.
        # WARNING: Operations are already indexed at this point.
        api_spec = self.api.api_spec
        if self.has_plugin(PluginRequirement("core", max="3.20.0")):
            for method, path in self.api.operations.values():
                operation = api_spec["paths"][path][method]
                if method == "get" and "parameters" in operation:
                    for parameter in operation["parameters"]:
                        if (
                            parameter["name"] == "ordering"
                            and parameter["in"] == "query"
                            and "schema" in parameter
                            and parameter["schema"]["type"] == "string"
                        ):
                            parameter["schema"] = {"type": "array", "items": {"type": "string"}}
                            parameter["explode"] = False
                            parameter["style"] = "form"
        if self.has_plugin(PluginRequirement("core", max="3.22.0.dev")):
            for method, path in self.api.operations.values():
                operation = api_spec["paths"][path][method]
                if method == "get" and "parameters" in operation:
                    for parameter in operation["parameters"]:
                        if (
                            parameter["name"] in ["fields", "exclude_fields"]
                            and parameter["in"] == "query"
                            and "schema" in parameter
                            and parameter["schema"]["type"] == "string"
                        ):
                            parameter["schema"] = {"type": "array", "items": {"type": "string"}}
        if self.has_plugin(PluginRequirement("file", max="1.11.0")):
            operation = api_spec["paths"]["{file_file_alternate_content_source_href}refresh/"][
                "post"
            ]
            operation.pop("requestBody")
        if self.has_plugin(
            PluginRequirement("python", max="99.99.0.dev")
        ):  # TODO Add version bounds
            python_remote_serializer = api_spec["components"]["schemas"]["python.PythonRemote"]
            patched_python_remote_serializer = api_spec["components"]["schemas"][
                "Patchedpython.PythonRemote"
            ]
            for prop in ("includes", "excludes"):
                python_remote_serializer["properties"][prop]["type"] = "array"
                python_remote_serializer["properties"][prop]["items"] = {"type": "string"}
                patched_python_remote_serializer["properties"][prop]["type"] = "array"
                patched_python_remote_serializer["properties"][prop]["items"] = {"type": "string"}

    @property
    def api(self) -> OpenAPI:
        if self._api is None:
            if self._api_kwargs.get("username") and not self._api_kwargs.get("password"):
                self._api_kwargs["password"] = self.prompt("password", hide_input=True)
            try:
                self._api = OpenAPI(doc_path=f"{self.api_path}docs/api.json", **self._api_kwargs)
            except OpenAPIError as e:
                raise PulpException(str(e))
            # Rerun scheduled version checks
            for plugin in self._needed_plugins:
                self.needs_plugin(plugin)
            self._patch_api_spec()
        return self._api

    @property
    def component_versions(self) -> Dict[str, str]:
        result: Dict[str, str] = self.api.api_spec.get("info", {}).get("x-pulp-app-versions", {})
        return result

    def call(
        self,
        operation_id: str,
        non_blocking: bool = False,
        parameters: Optional[Dict[str, Any]] = None,
        body: Optional[EntityDefinition] = None,
        uploads: Optional[UploadsMap] = None,
        validate_body: bool = True,
    ) -> Any:
        """
        Perform an API call for operation_id.
        Wait for triggered tasks to finish if not background.
        Returns the operation result, or the finished task.
        If non_blocking, returns unfinished tasks.
        """
        if parameters is not None:
            parameters = preprocess_payload(parameters)
        if body is not None:
            body = preprocess_payload(body)
        # ---- SNIP ----
        # In the future we want everything as part of the body.
        if uploads:
            self.echo(
                _("Deprecated use of 'uploads' for operation '{operation_id}'").format(
                    operation_id=operation_id
                )
            )
            body = body or {}
            body.update(uploads)
        # ---- SNIP ----
        try:
            result = self.api.call(
                operation_id,
                parameters=parameters,
                body=body,
                validate_body=validate_body,
            )
        except OpenAPIError as e:
            raise PulpException(str(e))
        except HTTPError as e:
            raise PulpException(str(e.response.text))
        # Asynchronous tasks seem to be reported by a dict containing only one key "task"
        if isinstance(result, dict) and ["task"] == list(result.keys()):
            task_href = result["task"]
            result = self.api.call("tasks_read", parameters={"task_href": task_href})
            self.echo(
                _("Started background task {task_href}").format(task_href=task_href), err=True
            )
            if not non_blocking:
                result = self.wait_for_task(result)
        if isinstance(result, dict) and ["task_group"] == list(result.keys()):
            task_group_href = result["task_group"]
            result = self.api.call(
                "task_groups_read", parameters={"task_group_href": task_group_href}
            )
            self.echo(
                _("Started background task group {task_group_href}").format(
                    task_group_href=task_group_href
                ),
                err=True,
            )
            if not non_blocking:
                result = self.wait_for_task_group(result)
        return result

    @classmethod
    def _check_task_finished(cls, task: EntityDefinition) -> bool:
        task_href = task["pulp_href"]

        if task["state"] == "completed":
            return True
        elif task["state"] == "failed":
            raise PulpException(
                _("Task {task_href} failed: '{description}'").format(
                    task_href=task_href,
                    description=task["error"].get("description") or task["error"].get("reason"),
                )
            )
        elif task["state"] == "canceled":
            raise PulpException(_("Task {task_href} canceled").format(task_href=task_href))
        elif task["state"] in ["waiting", "running", "canceling"]:
            return False
        else:
            raise NotImplementedError(_("Unknown task state: {state}").format(state=task["state"]))

    def _poll_task(self, task: EntityDefinition) -> EntityDefinition:
        while True:
            if self._check_task_finished(task):
                self.echo("Done.", err=True)
                return task
            else:
                if self.timeout:
                    assert isinstance(self.start_time, datetime.datetime)
                    if (datetime.datetime.now() - self.start_time).seconds > self.timeout:
                        raise PulpNoWait(
                            _("Waiting for task {task_href} timed out.").format(
                                task_href=task["pulp_href"]
                            )
                        )
                time.sleep(1)
                self.echo(".", nl=False, err=True)
                task = self.api.call("tasks_read", parameters={"task_href": task["pulp_href"]})

    def wait_for_task(self, task: EntityDefinition) -> Any:
        """
        Wait for a task to finish and return the finished task object.

        Raise `PulpNoWait` on timeout, background, ctrl-c, if task failed or was canceled.
        """
        self.start_time = datetime.datetime.now()

        if self.background_tasks:
            raise PulpNoWait(_("Not waiting for task because --background was specified."))
        task_href = task["pulp_href"]
        try:
            return self._poll_task(task)
        except KeyboardInterrupt:
            raise PulpNoWait(_("Task {task_href} sent to background.").format(task_href=task_href))

    def wait_for_task_group(self, task_group: EntityDefinition) -> Any:
        """
        Wait for a task group to finish and return the finished task object.

        Raise `PulpNoWait` on timeout, background, ctrl-c, if tasks failed or were canceled.
        """
        self.start_time = datetime.datetime.now()

        if self.background_tasks:
            raise PulpNoWait("Not waiting for task group because --background was specified.")
        try:
            while True:
                if task_group["all_tasks_dispatched"] is True:
                    for task in task_group["tasks"]:
                        task = self.api.call(
                            "tasks_read", parameters={"task_href": task["pulp_href"]}
                        )
                        self.echo(
                            _("Waiting for task {task_href}").format(task_href=task["pulp_href"]),
                            err=True,
                        )
                        self._poll_task(task)
                    return task_group
                else:
                    if self.timeout:
                        assert isinstance(self.start_time, datetime.datetime)
                        if (datetime.datetime.now() - self.start_time).seconds > self.timeout:
                            raise PulpNoWait(
                                _("Waiting for task group {task_group_href} timed out.").format(
                                    task_group_href=task_group["pulp_href"]
                                )
                            )
                    time.sleep(1)
                    self.echo(".", nl=False, err=True)
                    task_group = self.api.call(
                        "task_groups_read", parameters={"task_group_href": task_group["pulp_href"]}
                    )
        except KeyboardInterrupt:
            raise PulpNoWait(
                _("Task group {task_group_href} sent to background.").format(
                    task_group_href=task_group["pulp_href"]
                )
            )

    def has_plugin(
        self,
        plugin: PluginRequirement,
    ) -> bool:
        if not self.component_versions:
            # Prior to 3.9 we do not have this information.
            # Assume we have no plugin installed.
            return not plugin.inverted
        version: Optional[str] = self.component_versions.get(plugin.name)
        if version is None:
            return plugin.inverted
        if plugin.min is not None:
            if parse_version(version) < parse_version(plugin.min):
                return plugin.inverted
        if plugin.max is not None:
            if parse_version(version) >= parse_version(plugin.max):
                return plugin.inverted
        return not plugin.inverted

    def needs_plugin(
        self,
        plugin: PluginRequirement,
    ) -> None:
        if self._api is not None:
            if not self.has_plugin(plugin):
                specifier = plugin.name
                separator = ""
                if plugin.min is not None:
                    specifier += f">={plugin.min}"
                    separator = ","
                if plugin.max is not None:
                    specifier += f"{separator}<{plugin.max}"
                feature = plugin.feature or _("this command")
                if plugin.inverted:
                    msg = _(
                        "The server provides the pulp component '{specifier}',"
                        " which prevents the use of {feature}."
                        " See 'pulp status' for installed components."
                    )
                else:
                    msg = _(
                        "The server does not provide the pulp component '{specifier}',"
                        " which is needed to use {feature}."
                        " See 'pulp status' for installed components."
                    )
                raise PulpException(msg.format(specifier=specifier, feature=feature))
        else:
            # Schedule for later checking
            self._needed_plugins.append(plugin)


class PulpEntityContext:
    """
    Base class for entity specific contexts.
    This class provides the basic CRUD commands and ties its instances to the global
    PulpContext for api access.
    """

    # Subclasses should provide appropriate values here
    ENTITY: ClassVar[str] = _("entity")
    ENTITIES: ClassVar[str] = _("entities")
    HREF: ClassVar[str]
    ID_PREFIX: ClassVar[str]
    # Set of fields that can be cleared by sending 'null'
    NULLABLES: ClassVar[Set[str]] = set()
    # List of necessary plugin to operate such an entity in the server
    NEEDS_PLUGINS: ClassVar[List[PluginRequirement]] = []
    # Subclasses can specify version dependent capabilities here
    # e.g. `CAPABILITIES = {
    #           "feature1": [
    #               PluginRequirement("file"),
    #               PluginRequirement("core", min_version="3.7.0")
    #           ]
    #       }
    CAPABILITIES: ClassVar[Dict[str, List[PluginRequirement]]] = {}
    HREF_PATTERN: str

    # Hidden values for the lazy entity lookup
    _entity: Optional[EntityDefinition]
    _entity_lookup: EntityDefinition

    # Subclasses for nested entities can define the parameters for there parent scope here
    @property
    def scope(self) -> Dict[str, Any]:
        return {}

    @property
    def entity(self) -> EntityDefinition:
        """
        Entity property that will perform a lazy lookup once it is accessed.
        You can specify lookup parameters by assigning a dictionary to it,
        or assign an href to the ``pulp_href`` property.
        To reset to having no attached entity you can assign ``None``.
        Assigning to it will reset the lazy lookup behaviour.
        """
        if self._entity is None:
            if not self._entity_lookup:
                raise PulpException(
                    _("A {entity} must be specified for this command.").format(entity=self.ENTITY)
                )
            if self._entity_lookup.get("pulp_href"):
                self._entity = self.show(self._entity_lookup["pulp_href"])
            else:
                self._entity = self.find(**self._entity_lookup)
            self._entity_lookup = {}
        return self._entity

    @entity.setter
    def entity(self, value: Optional[EntityDefinition]) -> None:
        # Setting this property will always (lazily) retrigger retrieving the entity.
        # If set multiple times in a row without reading, the criteria will be added.
        if value is None:
            self._entity_lookup = {}
        else:
            self._entity_lookup.update(value)
            self._entity_lookup.pop("pulp_href", None)
        self._entity = None

    @property
    def pulp_href(self) -> str:
        """
        Property to represent the href of the attached entity.
        Assigning to it will reset the lazy lookup behaviour.
        """
        return str(self.entity["pulp_href"])

    @pulp_href.setter
    def pulp_href(self, value: str) -> None:
        if not href_regex.fullmatch(value):
            raise PulpException(
                _("'{value}' is not a valid HREF value for a {context_id}").format(
                    value=value, context_id=self.ENTITY
                )
            )

        # Setting this property will always (lazily) retrigger retrieving the entity.
        self._entity_lookup = {"pulp_href": value}
        self._entity = None

    def __init__(
        self,
        pulp_ctx: PulpContext,
        pulp_href: Optional[str] = None,
        entity: Optional[EntityDefinition] = None,
    ) -> None:
        assert pulp_href is None or entity is None

        self.meta: Dict[str, str] = {}
        self.pulp_ctx: PulpContext = pulp_ctx

        # Add requirements to the lazy evaluated list
        for req in self.NEEDS_PLUGINS:
            self.pulp_ctx.needs_plugin(req)

        self._entity = None
        if pulp_href is None:
            self._entity_lookup = entity or {}
        else:
            self.pulp_href = pulp_href

    def call(
        self,
        operation: str,
        non_blocking: bool = False,
        parameters: Optional[Dict[str, Any]] = None,
        body: Optional[EntityDefinition] = None,
        uploads: Optional[UploadsMap] = None,
        validate_body: bool = True,
    ) -> Any:
        operation_id: str = (
            getattr(self, operation.upper() + "_ID", None) or self.ID_PREFIX + "_" + operation
        )
        return self.pulp_ctx.call(
            operation_id,
            non_blocking=non_blocking,
            parameters=parameters,
            body=body,
            uploads=uploads,
            validate_body=validate_body,
        )

    @classmethod
    def _preprocess_value(cls, key: str, value: Any) -> Any:
        if key in cls.NULLABLES and value == "":
            return None
        return _preprocess_value(value)

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        # This function is deprecated. Subclasses should subclass `preprocess_entity` instead.
        #
        # TODO once the transition is done, just keep this implementation as `preprocess_entity`
        if isinstance(body, PreprocessedEntityDefinition):
            return body

        return PreprocessedEntityDefinition(
            {
                key: self._preprocess_value(key, value)
                for key, value in body.items()
                if value is not None
            }
        )

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        return self.preprocess_body(body)

    def list(self, limit: int, offset: int, parameters: Dict[str, Any]) -> List[Any]:
        count: int = -1
        entities: List[Any] = []
        payload: Dict[str, Any] = parameters.copy()
        payload.update(self.scope)
        payload["offset"] = offset
        payload["limit"] = BATCH_SIZE
        while limit != 0:
            if limit > BATCH_SIZE:
                limit -= BATCH_SIZE
            else:
                payload["limit"] = limit
                limit = 0
            result: Mapping[str, Any] = self.call("list", parameters=payload)
            count = result["count"]
            entities.extend(result["results"])
            if result["next"] is None:
                break
            payload["offset"] += payload["limit"]
        else:
            self.pulp_ctx.echo(
                _("Not all {count} entries were shown.").format(count=count), err=True
            )
        return entities

    def find(self, **kwargs: Any) -> Any:
        search_result = self.list(limit=1, offset=0, parameters=kwargs)
        if len(search_result) != 1:
            raise PulpException(
                _("Could not find {entity} with {kwargs}.").format(
                    entity=self.ENTITY, kwargs=kwargs
                )
            )
        return search_result[0]

    def show(self, href: Optional[str] = None) -> Any:
        return self.call("read", parameters={self.HREF: href or self.pulp_href})

    def create(
        self,
        body: EntityDefinition,
        parameters: Optional[Mapping[str, Any]] = None,
        uploads: Optional[UploadsMap] = None,
        non_blocking: bool = False,
    ) -> Any:
        _parameters = self.scope
        if parameters:
            _parameters.update(parameters)
        if body is not None:
            body = self.preprocess_entity(body, partial=False)
        result = self.call(
            "create",
            parameters=_parameters,
            body=body,
            uploads=uploads,
            non_blocking=non_blocking,
        )
        if not non_blocking and result["pulp_href"].startswith(self.pulp_ctx.api_path + "tasks/"):
            result = self.show(result["created_resources"][0])
        return result

    def update(
        self,
        href: Optional[str] = None,
        body: Optional[EntityDefinition] = None,
        parameters: Optional[Mapping[str, Any]] = None,
        uploads: Optional[UploadsMap] = None,
        non_blocking: bool = False,
    ) -> Any:
        # Workaround for plugins that do not have ID_PREFIX in place
        if hasattr(self, "UPDATE_ID") and not hasattr(self, "PARTIAL_UPDATE_ID"):
            self.PARTIAL_UPDATE_ID = getattr(self, "UPDATE_ID")
        # ----------------------------------------------------------
        _parameters = {self.HREF: href or self.pulp_href}
        if parameters:
            _parameters.update(parameters)
        if body is not None:
            body = self.preprocess_entity(body, partial=False)
        return self.call(
            "partial_update",
            parameters=_parameters,
            body=body,
            uploads=uploads,
            non_blocking=non_blocking,
        )

    def delete(self, href: Optional[str] = None, non_blocking: bool = False) -> Any:
        return self.call(
            "delete", parameters={self.HREF: href or self.pulp_href}, non_blocking=non_blocking
        )

    def set_label(self, key: str, value: str, non_blocking: bool = False) -> Any:
        # We would have a dedicated api for this ideally.
        labels = self.entity["pulp_labels"]
        labels[key] = value
        return self.update(body={"pulp_labels": labels}, non_blocking=non_blocking)

    def unset_label(self, key: str, non_blocking: bool = False) -> Any:
        # We would have a dedicated api for this ideally.
        labels = self.entity["pulp_labels"]
        try:
            labels.pop(key)
        except KeyError:
            raise PulpException(_("Could not find label with key '{key}'.").format(key=key))
        return self.update(body={"pulp_labels": labels}, non_blocking=non_blocking)

    def show_label(self, key: str) -> Any:
        # We would have a dedicated api for this ideally.
        labels = self.entity["pulp_labels"]
        try:
            return labels[key]
        except KeyError:
            raise PulpException(_("Could not find label with key '{key}'.").format(key=key))

    def my_permissions(self) -> Any:
        self.needs_capability("roles")
        return self.call("my_permissions", parameters={self.HREF: self.pulp_href})

    def list_roles(self) -> Any:
        self.needs_capability("roles")
        return self.call("list_roles", parameters={self.HREF: self.pulp_href})

    def add_role(self, role: str, users: List[str], groups: List[str]) -> Any:
        self.needs_capability("roles")
        return self.call(
            "add_role",
            parameters={self.HREF: self.pulp_href},
            body={"role": role, "users": users, "groups": groups},
        )

    def remove_role(self, role: str, users: List[str], groups: List[str]) -> Any:
        self.needs_capability("roles")
        return self.call(
            "remove_role",
            parameters={self.HREF: self.pulp_href},
            body={"role": role, "users": users, "groups": groups},
        )

    def capable(self, capability: str) -> bool:
        return capability in self.CAPABILITIES and all(
            (self.pulp_ctx.has_plugin(pr) for pr in self.CAPABILITIES[capability])
        )

    def needs_capability(self, capability: str) -> None:
        if capability in self.CAPABILITIES:
            for pr in self.CAPABILITIES[capability]:
                self.pulp_ctx.needs_plugin(pr)
        else:
            raise PulpException(
                _("Capability '{capability}' needed on '{entity}' for this command.").format(
                    capability=capability, entity=self.ENTITY
                )
            )


class PulpRemoteContext(PulpEntityContext):
    """
    Base class for remote specific contexts.
    """

    ENTITY = _("remote")
    ENTITIES = _("remotes")
    ID_PREFIX = "remotes"
    HREF_PATTERN = r"remotes/(?P<plugin>[\w\-_]+)/(?P<resource_type>[\w\-_]+)/"
    NULLABLES = {
        "ca_cert",
        "client_cert",
        "client_key",
        "username",
        "password",
        "proxy_url",
        "proxy_username",
        "proxy_password",
        "download_concurrency",
        "max_retries",
        "total_timeout",
        "connect_timeout",
        "sock_connect_timeout",
        "sock_read_timeout",
        "rate_limit",
    }


class PulpDistributionContext(PulpEntityContext):
    ENTITY = _("distribution")
    ENTITIES = _("distributions")
    ID_PREFIX = "distributions"
    HREF_PATTERN = r"distributions/(?P<plugin>[\w\-_]+)/(?P<resource_type>[\w\-_]+)/"


class PulpRepositoryVersionContext(PulpEntityContext):
    """
    Base class for repository version specific contexts.
    This class provides the basic CRUD commands and
    ties its instances to the global PulpContext for api access.
    """

    ENTITY = _("repository version")
    ENTITIES = _("repository versions")
    repository_ctx: "PulpRepositoryContext"

    def __init__(self, pulp_ctx: PulpContext, repository_ctx: "PulpRepositoryContext") -> None:
        super().__init__(pulp_ctx)
        self.repository_ctx = repository_ctx

    @property
    def scope(self) -> Dict[str, Any]:
        return {self.repository_ctx.HREF: self.repository_ctx.pulp_href}

    def repair(self, href: Optional[str] = None) -> Any:
        return self.call("repair", parameters={self.HREF: href or self.pulp_href}, body={})


class PulpRepositoryContext(PulpEntityContext):
    """
    Base class for repository specific contexts.
    This class provides the basic CRUD commands as well as synchronizing and
    ties its instances to the global PulpContext for api access.
    """

    ENTITY = _("repository")
    ENTITIES = _("repositories")
    HREF_PATTERN = r"repositories/(?P<plugin>[\w\-_]+)/(?P<resource_type>[\w\-_]+)/"
    ID_PREFIX = "repositories"
    VERSION_CONTEXT: ClassVar[Type[PulpRepositoryVersionContext]]
    NULLABLES = {"description", "retain_repo_versions"}

    def get_version_context(self) -> PulpRepositoryVersionContext:
        return self.VERSION_CONTEXT(self.pulp_ctx, self)

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if self.pulp_ctx.has_plugin(PluginRequirement("core", "3.13.0", "3.15.0")):
            # "retain_repo_versions" has been named "retained_versions" until pulpcore 3.15
            # https://github.com/pulp/pulpcore/pull/1472
            if "retain_repo_versions" in body:
                body["retained_versions"] = body.pop("retain_repo_versions")
        return body

    def sync(self, href: Optional[str] = None, body: Optional[EntityDefinition] = None) -> Any:
        return self.call("sync", parameters={self.HREF: href or self.pulp_href}, body=body or {})

    def modify(
        self,
        href: Optional[str] = None,
        add_content: Optional[List[str]] = None,
        remove_content: Optional[List[str]] = None,
        base_version: Optional[str] = None,
    ) -> Any:
        body: Dict[str, Any] = {}
        if add_content is not None:
            body["add_content_units"] = add_content
        if remove_content is not None:
            body["remove_content_units"] = remove_content
        if base_version is not None:
            body["base_version"] = base_version
        return self.call("modify", parameters={self.HREF: href or self.pulp_href}, body=body)


class PulpContentContext(PulpEntityContext):
    """
    Base class for content specific contexts
    """

    ENTITY = _("content")
    ENTITIES = _("content")
    ID_PREFIX = "content"


class PulpACSContext(PulpEntityContext):
    ENTITY = _("ACS")
    ENTITIES = _("ACSes")
    HREF_PATTERN = r"acs/(?P<plugin>[\w\-_]+)/(?P<resource_type>[\w\-_]+)/"
    ID_PREFIX = "acs"

    def refresh(self, href: Optional[str] = None) -> Any:
        return self.call("refresh", parameters={self.HREF: href or self.pulp_href})


EntityFieldDefinition = Union[None, str, PulpEntityContext]


##############################################################################
# Registries for Contexts of different sorts
# A command can use these to identify e.g. all repository types known to the CLI
# Note that it will only be fully populated, once all plugins are loaded.


registered_repository_contexts: Dict[str, Type[PulpRepositoryContext]] = {}
