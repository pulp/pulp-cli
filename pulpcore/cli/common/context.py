import datetime
import gettext
import json
import sys
import time
from typing import (
    IO,
    Any,
    ClassVar,
    Dict,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    overload,
)

import click
import yaml
from packaging.version import parse as parse_version
from requests import HTTPError
from urllib3.util import parse_url

from pulpcore.cli.common.openapi import OpenAPI, OpenAPIError

try:
    from pygments import highlight
    from pygments.formatters import Terminal256Formatter
    from pygments.lexers import JsonLexer, YamlLexer
except ImportError:
    PYGMENTS = False
else:
    PYGMENTS = True
    PYGMENTS_STYLE = "solarized-dark"

_ = gettext.gettext

DEFAULT_LIMIT = 25
BATCH_SIZE = 25


EntityDefinition = Dict[str, Any]
RepositoryDefinition = Tuple[str, str]  # name, pulp_type
RepositoryVersionDefinition = Tuple[str, str, int]  # name, pulp_type, version


class PluginRequirement(NamedTuple):
    name: str
    min: Optional[str] = None
    max: Optional[str] = None
    feature: Optional[str] = None


new_component_names_to_pre_3_11_names: Dict[str, str] = dict(
    ansible="pulp_ansible",
    container="pulp_container",
    core="pulpcore",
    deb="pulp_deb",
    file="pulp_file",
    python="pulp_python",
    rpm="pulp_rpm",
)


class PulpNoWait(click.ClickException):
    exit_code = 0

    def show(self, file: Optional[IO[str]] = None) -> None:
        """
        Format the message into file or STDERR.
        Overwritten from base class to not print "Error: ".
        """
        if file is None:
            file = click.get_text_stream("stderr")
        click.echo(self.format_message(), file=file)


class PulpJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return super().default(obj)


class PulpContext:
    """
    Class for the global PulpContext object.
    It is an abstraction layer for api access and output handling.
    """

    def __init__(self, api_kwargs: Dict[str, Any], format: str, background_tasks: bool) -> None:
        self._api: Optional[OpenAPI] = None
        self._api_kwargs = api_kwargs
        self._needed_plugins: List[PluginRequirement] = []
        self.isatty: bool = sys.stdout.isatty()

        self.format: str = format
        self.background_tasks: bool = background_tasks

    @property
    def api(self) -> OpenAPI:
        if self._api is None:
            if self._api_kwargs.get("username") and not self._api_kwargs.get("password"):
                self._api_kwargs["password"] = click.prompt("password", hide_input=True)
            try:
                self._api = OpenAPI(**self._api_kwargs)
            except OpenAPIError as e:
                raise click.ClickException(str(e))
            # Rerun scheduled version checks
            for plugin in self._needed_plugins:
                self.needs_plugin(plugin.name, plugin.min, plugin.max, plugin.feature)
        return self._api

    @property
    def component_versions(self) -> Dict[str, str]:
        result: Dict[str, str] = self.api.api_spec.get("info", {}).get("x-pulp-app-versions", {})
        return result

    def output_result(self, result: Any) -> None:
        """
        Dump the provided result to the console using the selected renderer
        """
        if self.format == "json":
            output = json.dumps(result, cls=PulpJSONEncoder, indent=(2 if self.isatty else None))
            if PYGMENTS and self.isatty:
                output = highlight(output, JsonLexer(), Terminal256Formatter(style=PYGMENTS_STYLE))
            click.echo(output)
        elif self.format == "yaml":
            output = yaml.dump(result)
            if PYGMENTS and self.isatty:
                output = highlight(output, YamlLexer(), Terminal256Formatter(style=PYGMENTS_STYLE))
            click.echo(output)
        elif self.format == "none":
            pass
        else:
            raise NotImplementedError(f"Format '{self.format}' not implemented.")

    def call(self, operation_id: str, non_blocking: bool = False, *args: Any, **kwargs: Any) -> Any:
        """
        Perform an API call for operation_id.
        Wait for triggered tasks to finish if not background.
        Returns the operation result, or the finished task.
        If non_blocking, returns unfinished tasks.
        """
        try:
            result = self.api.call(operation_id, *args, **kwargs)
        except OpenAPIError as e:
            raise click.ClickException(str(e))
        except HTTPError as e:
            raise click.ClickException(str(e.response.text))
        # Asynchronous tasks seem to be reported by a dict containing only one key "task"
        if isinstance(result, dict) and ["task"] == list(result.keys()):
            task_href = result["task"]
            result = self.api.call("tasks_read", parameters={"task_href": task_href})
            click.echo(f"Started background task {task_href}", err=True)
            if not non_blocking:
                result = self.wait_for_task(result)
        return result

    def wait_for_task(self, task: EntityDefinition, timeout: int = 120) -> Any:
        """
        Wait for a task to finish and return the finished task object.
        Raise `click.ClickException` on timeout, background, ctrl-c, if task failed or was canceled.
        """
        if self.background_tasks:
            raise PulpNoWait("Not waiting for task because --background was specified.")
        task_href = task["pulp_href"]
        try:
            while True:
                if task["state"] == "completed":
                    click.echo("Done.", err=True)
                    return task
                elif task["state"] == "failed":
                    raise click.ClickException(
                        f"Task {task_href} failed: '{task['error']['description']}'"
                    )
                elif task["state"] == "canceled":
                    raise click.ClickException("Task canceled")
                elif task["state"] in ["waiting", "running"]:
                    if timeout <= 0:
                        return task
                    time.sleep(1)
                    timeout -= 1
                    click.echo(".", nl=False, err=True)
                    task = self.api.call("tasks_read", parameters={"task_href": task_href})
                else:
                    raise NotImplementedError(f"Unknown task state: {task['state']}")
            raise click.ClickException("Task timed out")
        except KeyboardInterrupt:
            raise PulpNoWait(f"Task {task_href} sent to background.")

    @overload
    def has_plugin(
        self,
        plugin: str,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
    ) -> bool:
        ...

    @overload
    def has_plugin(
        self,
        plugin: PluginRequirement,
        min_version: None = None,
        max_version: None = None,
    ) -> bool:
        ...

    def has_plugin(
        self,
        plugin: Union[PluginRequirement, str],
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
    ) -> bool:
        if not isinstance(plugin, PluginRequirement):
            plugin = PluginRequirement(plugin, min_version, max_version)
        if not self.component_versions:
            # Prior to 3.9 we do not have this information
            # assume yes if no version constraint is specified
            return (plugin.min is None) and (plugin.max is None)
        version: Optional[str] = self.component_versions.get(plugin.name)
        if version is None:
            pre_3_11_name: str = new_component_names_to_pre_3_11_names.get(plugin.name, "")
            version = self.component_versions.get(pre_3_11_name)
            if version is None:
                return False
        if plugin.min is not None:
            if parse_version(version) < parse_version(plugin.min):
                return False
        if plugin.max is not None:
            if parse_version(version) >= parse_version(plugin.max):
                return False
        return True

    @overload
    def needs_plugin(
        self,
        plugin: str,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        feature: Optional[str] = None,
    ) -> None:
        ...

    @overload
    def needs_plugin(
        self,
        plugin: PluginRequirement,
        min_version: None = None,
        max_version: None = None,
        feature: None = None,
    ) -> None:
        ...

    def needs_plugin(
        self,
        plugin: Union[PluginRequirement, str],
        min_version: Optional[str] = None,
        max_version: Optional[str] = None,
        feature: Optional[str] = None,
    ) -> None:
        if not isinstance(plugin, PluginRequirement):
            plugin = PluginRequirement(plugin, min_version, max_version, feature)
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
                raise click.ClickException(
                    _(
                        "The server does not have '{specifier}' installed,"
                        " which is needed to use {feature}."
                    ).format(specifier=specifier, feature=feature)
                )
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
    ENTITY: ClassVar[str] = "entity"
    ENTITIES: ClassVar[str] = "entities"
    HREF: ClassVar[str]
    LIST_ID: ClassVar[str]
    READ_ID: ClassVar[str]
    CREATE_ID: ClassVar[str]
    UPDATE_ID: ClassVar[str]
    DELETE_ID: ClassVar[str]
    NULLABLES: ClassVar[Set[str]] = set()

    # Hidden values for the lazy entity lookup
    _entity: Optional[EntityDefinition]
    _entity_lookup: EntityDefinition

    # { "pulp_type" : repository-list-id }
    REPOSITORY_FIND_IDS: Dict[str, str] = {
        "file": "repositories_file_file_list",
        "rpm": "repositories_rpm_rpm_list",
    }
    # { "pulp_type" : repository-version-list-id }
    REPOSITORY_VERSION_FIND_IDS: Dict[str, str] = {
        "file": "repositories_file_file_versions_list",
        "rpm": "repositories_rpm_rpm_versions_list",
    }
    # { "pulp_type" : repository-href-ids }
    REPOSITORY_HREF_IDS = {
        "file": "file_file_repository_href",
        "rpm": "rpm_rpm_repository_href",
    }

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
                raise click.ClickException(f"A {self.ENTITY} must be specified for this command.")
            if "pulp_href" in self._entity_lookup:
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
        self._entity = None
        if pulp_href is None:
            self._entity_lookup = entity or {}
        else:
            self.pulp_href = pulp_href

    def _preprocess_value(self, key: str, value: Any) -> Any:
        if key in self.NULLABLES and value == "":
            return None
        if isinstance(value, PulpEntityContext):
            return value.pulp_href
        return value

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        return {
            key: self._preprocess_value(key, value)
            for key, value in body.items()
            if value is not None
        }

    def list(self, limit: int, offset: int, parameters: Dict[str, Any]) -> List[Any]:
        count: int = -1
        entities: List[Any] = []
        payload: Dict[str, Any] = self.scope
        payload.update(parameters.copy())
        payload["offset"] = offset
        payload["limit"] = BATCH_SIZE
        while limit != 0:
            if limit > BATCH_SIZE:
                limit -= BATCH_SIZE
            else:
                payload["limit"] = limit
                limit = 0
            result: Dict[str, Any] = self.pulp_ctx.call(self.LIST_ID, parameters=payload)
            count = result["count"]
            entities.extend(result["results"])
            if result["next"] is None:
                break
            payload["offset"] += payload["limit"]
        else:
            click.echo(f"Not all {count} entries were shown.", err=True)
        return entities

    def find(self, **kwargs: Any) -> Any:
        search_result = self.list(limit=1, offset=0, parameters=kwargs)
        if len(search_result) != 1:
            raise click.ClickException(f"Could not find {self.ENTITY} with {kwargs}.")
        return search_result[0]

    def show(self, href: str) -> Any:
        return self.pulp_ctx.call(self.READ_ID, parameters={self.HREF: href})

    def create(
        self,
        body: EntityDefinition,
        parameters: Optional[Dict[str, Any]] = None,
        non_blocking: bool = False,
    ) -> Any:
        _parameters = self.scope
        if parameters:
            _parameters.update(parameters)
        result = self.pulp_ctx.call(
            self.CREATE_ID, parameters=_parameters, body=body, non_blocking=non_blocking
        )
        if not non_blocking and result["pulp_href"].startswith("/pulp/api/v3/tasks/"):
            result = self.show(result["created_resources"][0])
        return result

    def update(
        self,
        href: str,
        body: EntityDefinition,
        parameters: Optional[Dict[str, Any]] = None,
        uploads: Optional[Dict[str, Any]] = None,
        non_blocking: bool = False,
    ) -> Any:
        _parameters = {self.HREF: href}
        if parameters:
            _parameters.update(parameters)
        return self.pulp_ctx.call(
            self.UPDATE_ID,
            parameters=_parameters,
            body=body,
            uploads=uploads,
            non_blocking=non_blocking,
        )

    def delete(self, href: str, non_blocking: bool = False) -> Any:
        return self.pulp_ctx.call(
            self.DELETE_ID, parameters={self.HREF: href}, non_blocking=non_blocking
        )

    def set_label(self, href: str, key: str, value: str, non_blocking: bool = False) -> Any:
        labels = self.show(href)["pulp_labels"]
        labels[key] = value
        return self.update(href, body={"pulp_labels": labels}, non_blocking=non_blocking)

    def unset_label(self, href: str, key: str, non_blocking: bool = False) -> Any:
        labels = self.show(href)["pulp_labels"]
        labels.pop(key)
        return self.update(href, body={"pulp_labels": labels}, non_blocking=non_blocking)

    def show_label(self, href: str, key: str) -> Any:
        entity = self.show(href)
        try:
            return entity["pulp_labels"][key]
        except KeyError:
            raise click.ClickException(f"Could not find label with key '{key}'.")

    def find_repository(self, definition: RepositoryDefinition) -> Any:
        name, repo_type = definition
        if repo_type in self.REPOSITORY_FIND_IDS:
            search_result = self.pulp_ctx.call(
                self.REPOSITORY_FIND_IDS[repo_type], parameters={"name": name, "limit": 1}
            )
        else:
            raise click.ClickException(
                f"PulpExporter 'Repository-type '{repo_type}' not supported!"
            )

        if search_result["count"] != 1:
            raise click.ClickException(f"Repository '{name}/{repo_type}' not found.")

        repository = search_result["results"][0]
        return repository

    def find_repository_version(self, definition: RepositoryVersionDefinition) -> Any:
        name, repo_type, number = definition
        repo_href = self.find_repository((name, repo_type))["pulp_href"]
        if repo_type in self.REPOSITORY_VERSION_FIND_IDS:
            params = {self.REPOSITORY_HREF_IDS[repo_type]: repo_href, "number": number, "limit": 1}
            search_result = self.pulp_ctx.call(
                self.REPOSITORY_VERSION_FIND_IDS[repo_type], parameters=params
            )
        else:
            raise click.ClickException(
                f"PulpExporter 'Repository-type '{repo_type}' not supported!"
            )

        if search_result["count"] != 1:
            raise click.ClickException(
                f"RepositoryVersion '{name}/{repo_type}/{number}' not found."
            )

        repo_version = search_result["results"][0]
        return repo_version


class PulpRemoteContext(PulpEntityContext):
    """
    Base class for remote specific contexts.
    """

    ENTITY = "remote"
    ENTITIES = "remotes"
    NULLABLES = {
        "ca_cert",
        "client_cert",
        "client_key",
        "password",
        "proxy_url",
        "username",
    }

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        body = super().preprocess_body(body)
        if not self.pulp_ctx.has_plugin("core", min_version="3.11.dev"):
            # proxy_username and proxy_password are separate fields starting with 3.11
            # https://pulp.plan.io/issues/8167
            proxy_username = body.pop("proxy_username", None)
            proxy_password = body.pop("proxy_password", None)
            if proxy_username or proxy_password:
                if "proxy_url" in body:
                    if proxy_username and proxy_password:
                        parsed_url = parse_url(body["proxy_url"])
                        body["proxy_url"] = parsed_url._replace(
                            auth=":".join([proxy_username, proxy_password])
                        ).url
                    else:
                        raise click.ClickException(
                            _("Proxy username and password can only be provided in conjunction.")
                        )
                else:
                    raise click.ClickException(
                        _("Proxy credentials can only be provided with a proxy url.")
                    )
        return body


class PulpRepositoryVersionContext(PulpEntityContext):
    """
    Base class for repository version specific contexts.
    This class provides the basic CRUD commands and
    ties its instances to the global PulpContext for api access.
    """

    ENTITY = "repository version"
    ENTITIES = "repository versions"
    REPAIR_ID: ClassVar[str]
    repository_ctx: "PulpRepositoryContext"

    def __init__(self, pulp_ctx: PulpContext, repository_ctx: "PulpRepositoryContext") -> None:
        super().__init__(pulp_ctx)
        self.repository_ctx = repository_ctx

    @property
    def scope(self) -> Dict[str, Any]:
        return {self.repository_ctx.HREF: self.repository_ctx.pulp_href}

    def repair(self, href: str) -> Any:
        return self.pulp_ctx.call(
            self.REPAIR_ID,
            parameters={self.HREF: href},
        )


class PulpRepositoryContext(PulpEntityContext):
    """
    Base class for repository specific contexts.
    This class provides the basic CRUD commands as well as synchronizing and
    ties its instances to the global PulpContext for api access.
    """

    ENTITY = "repository"
    ENTITIES = "repositories"
    LIST_ID = "repositories_list"
    SYNC_ID: ClassVar[str]
    MODIFY_ID: ClassVar[str]
    VERSION_CONTEXT: ClassVar[Type[PulpRepositoryVersionContext]]
    NULLABLES = {"description", "retained_versions"}

    def get_version_context(self) -> PulpRepositoryVersionContext:
        return self.VERSION_CONTEXT(self.pulp_ctx, self)

    def sync(self, href: str, body: Dict[str, Any]) -> Any:
        return self.pulp_ctx.call(
            self.SYNC_ID,
            parameters={self.HREF: href},
            body=body,
        )

    def modify(
        self,
        href: str,
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
        return self.pulp_ctx.call(
            self.MODIFY_ID,
            parameters={self.HREF: href},
            body=body,
        )


class PulpContentContext(PulpEntityContext):
    """
    Base class for content specific contexts
    """

    ENTITY = "content"
    ENTITIES = "content"
    LIST_ID = "content_list"


EntityFieldDefinition = Union[None, str, PulpEntityContext]
##############################################################################
# Decorator to access certain contexts


pass_pulp_context = click.make_pass_decorator(PulpContext)
pass_entity_context = click.make_pass_decorator(PulpEntityContext)
pass_repository_context = click.make_pass_decorator(PulpRepositoryContext)
pass_repository_version_context = click.make_pass_decorator(PulpRepositoryVersionContext)
pass_content_context = click.make_pass_decorator(PulpContentContext)
