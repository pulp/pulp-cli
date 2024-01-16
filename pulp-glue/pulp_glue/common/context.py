import datetime
import os
import re
import sys
import time
import typing as t
from typing import IO, Any, ClassVar, Dict, List, Mapping, Optional, Set, Type, Union, cast

from packaging.specifiers import SpecifierSet
from requests import HTTPError

from pulp_glue.common.i18n import get_translation
from pulp_glue.common.openapi import OpenAPI, OpenAPIError

translation = get_translation(__package__)
_ = translation.gettext

DEFAULT_LIMIT = 25
BATCH_SIZE = 1000
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


class PluginRequirement:
    """
    A class to represent a Pulp plugin with a set of versions.

    This can be used in conjunction with `has_plugin(s)`, `needs_plugin(s)` and `CAPABILITIES`.
    The parameters `min` and `max` are deprecated.

    Parameters:
        name: The app-label of the pluin as reported by the status API.
        feature: A string being displayed as the feature if used with `needs_plugin` and the
            condition is not met.
        inverted: Treat the version set in specifier as inverted. If no specifier is provided, this
            describes the requirement of a plugin not being installed.
        specifier: A PEP-440 compatible version range.
        min: **[DEPRECATED]**
        max: **[DEPRECATED]**
    """

    def __init__(
        self,
        name: str,
        min: Optional[str] = None,
        max: Optional[str] = None,
        feature: Optional[str] = None,
        inverted: bool = False,
        specifier: Optional[Union[str, SpecifierSet]] = None,
    ):
        self.name = name
        self.feature = feature
        self.inverted = inverted
        if min is None and max is None:
            specifier = specifier or ""
        else:
            assert specifier is None
            specifier = ""
            separator = ""
            if min:
                specifier += f">={min}"
                separator = ","
            if max:
                specifier += f"{separator}<{max}"
        if isinstance(specifier, SpecifierSet):
            self.specifier = specifier
        else:
            self.specifier = SpecifierSet(specifier, prereleases=True)

    def __contains__(self, version: Optional[str]) -> bool:
        if version is None:
            return self.inverted
        return (version in self.specifier) != self.inverted

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name}{self.specifier})"

    __repr__ = __str__


class PulpException(Exception):
    """The base exception `pulp-glue` will emit on expected error paths."""

    pass


class PulpHTTPError(PulpException):
    """Exception to indicate HTTP error responses."""

    def __init__(self, msg: str, status_code: int) -> None:
        super().__init__(msg)
        self.status_code = status_code


class PulpNoWait(Exception):
    """Exception to indicate that a task continues running in the background."""

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


_REGISTERED_API_QUIRKS: t.List[t.Tuple[PluginRequirement, t.Callable[[OpenAPI], None]]] = []


def api_quirk(
    req: PluginRequirement,
) -> t.Callable[[t.Callable[[OpenAPI], None]], None]:
    """
    A function decorator to allow manipulating API specs based on the availability of plugins.

    Parameters:
        req: The plugin specifier to determine when the quirk should be applied.

    Examples:
        ```
        @api_quirk(PluginRequirement("catdog", specifier="<1.5.2"))
        def patch_barking_filter_type(api: OpenAPI) -> None:
            # fixup api.api_spec here
        ```
    """

    def _decorator(patch: t.Callable[[OpenAPI], None]) -> None:
        _REGISTERED_API_QUIRKS.append((req, patch))

    return _decorator


@api_quirk(PluginRequirement("core", specifier="<3.20.0"))
def patch_ordering_filters(api: OpenAPI) -> None:
    for method, path in api.operations.values():
        operation = api.api_spec["paths"][path][method]
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


@api_quirk(PluginRequirement("core", specifier="<3.22.0"))
def patch_field_select_filters(api: OpenAPI) -> None:
    for method, path in api.operations.values():
        operation = api.api_spec["paths"][path][method]
        if method == "get" and "parameters" in operation:
            for parameter in operation["parameters"]:
                if (
                    parameter["name"] in ["fields", "exclude_fields"]
                    and parameter["in"] == "query"
                    and "schema" in parameter
                    and parameter["schema"]["type"] == "string"
                ):
                    parameter["schema"] = {"type": "array", "items": {"type": "string"}}


@api_quirk(PluginRequirement("core", specifier="<99.99.0"))
def patch_content_in_query_filters(api: OpenAPI) -> None:
    # https://github.com/pulp/pulpcore/issues/3634
    for operation_id, (method, path) in api.operations.items():
        if (
            operation_id == "repository_versions_list"
            or (
                operation_id.startswith("repositories_") and operation_id.endswith("_versions_list")
            )
            or (operation_id.startswith("publications_") and operation_id.endswith("_list"))
        ):
            operation = api.api_spec["paths"][path][method]
            for parameter in operation["parameters"]:
                if (
                    parameter["name"] == "content__in"
                    and parameter["in"] == "query"
                    and "schema" in parameter
                    and parameter["schema"]["type"] == "string"
                ):
                    parameter["schema"] = {"type": "array", "items": {"type": "string"}}


@api_quirk(PluginRequirement("core", specifier=">=3.23,<3.30.0"))
def patch_upstream_pulp_replicate_request_body(api: OpenAPI) -> None:
    operation = api.api_spec["paths"]["{upstream_pulp_href}replicate/"]["post"]
    operation.pop("requestBody", None)


class PulpContext:
    """
    Abstract class for the global PulpContext object.
    It is an abstraction layer for api access and output handling.

    Parameters:
        api_root: The base url (excluding "api/v3/") to the servers api.
        api_kwargs: Extra arguments to pass to the wrapped `OpenAPI` object.
        background_tasks: Whether to wait for tasks. If `True`, all tasks triggered will
            immediately raise `PulpNoWait`.
        timeout: Limit of time to wait for unfinished tasks.
        domain: Name of the domain to interact with.
        format: **[DEPRECATED]**
    """

    def echo(self, message: str, nl: bool = True, err: bool = False) -> None:
        """
        Abstract function that will be called to emit warnings and task progress.

        Warning:
            This function needs to be implemented.
        """
        raise NotImplementedError("PulpContext is an abstract class.")

    def prompt(self, text: str, hide_input: bool = False) -> Any:
        """
        Abstract function that will be called to ask for a password interactively.

        Note:
            If a password is provided non-interactively, this function need not be implemented.
        """
        raise NotImplementedError("PulpContext is an abstract class.")

    def __init__(
        self,
        api_root: str,
        api_kwargs: Dict[str, Any],
        background_tasks: bool,
        timeout: Union[int, datetime.timedelta],
        domain: str = "default",
        format: Optional[str] = None,  # Deprecated
    ) -> None:
        self._api: Optional[OpenAPI] = None
        self._api_root: str = api_root
        self._api_kwargs = api_kwargs
        self._needed_plugins: List[PluginRequirement] = [
            PluginRequirement("core", specifier=">=3.11.0")
        ]
        self.isatty: bool = sys.stdout.isatty()
        self.pulp_domain: str = domain

        self.background_tasks: bool = background_tasks
        if isinstance(timeout, int):
            timeout = datetime.timedelta(seconds=timeout)
        self.timeout: datetime.timedelta = timeout

    def _patch_api_spec(self) -> None:
        # A place for last minute fixes to the api_spec.
        # WARNING: Operations are already indexed at this point.
        assert self._api is not None
        for req, patch in _REGISTERED_API_QUIRKS:
            if self.has_plugin(req):
                patch(self._api)

    @property
    def domain_enabled(self) -> bool:
        return cast(bool, self.api.api_spec.get("info", {}).get("x-pulp-domain-enabled", False))

    @property
    def api_path(self) -> str:
        if self.domain_enabled:
            return self._api_root + self.pulp_domain + "/api/v3/"
        return self._api_root + "api/v3/"

    @property
    def api(self) -> OpenAPI:
        """
        The lazy evaluated `OpenAPI` object contained in this context.

        This is only needed for low level interactions with the openapi spec.
        All calls to the API should be performed via `call`.
        """
        if self._api is None:
            if self._api_kwargs.get("username") and not self._api_kwargs.get("password"):
                self._api_kwargs["password"] = self.prompt("password", hide_input=True)
            try:
                self._api = OpenAPI(
                    doc_path=f"{self._api_root}api/v3/docs/api.json", **self._api_kwargs
                )
            except OpenAPIError as e:
                raise PulpException(str(e))
            # Rerun scheduled version checks
            for plugin_requirement in self._needed_plugins:
                self.needs_plugin(plugin_requirement)
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
        validate_body: bool = True,
    ) -> Any:
        """
        Perform an API call for operation_id.
        Wait for triggered tasks to finish if not background.
        Returns the operation result, or the finished task.

        Parameters:
            operation_id: The operation ID in the openapi v3 spec to be called.
            non_blocking: returns unfinished tasks if `True`.
            parameters: Arguments that are to be sent as headers, querystrings or part of the URI.
            body: Body payload for POST, PUT, PATCH calls.
            validate_body: Indicate whether the body should be validated.

        Returns:
            The body of the response, or the task or task group if one was issued.

        Raises:
            PulpNoWait: in case the context has `background_tasks` set or a task (group) timed out.
        """
        if parameters is None:
            parameters = {}
        if self.domain_enabled:
            # Validation will fail if path doesn't need domain parameter
            if "pulp_domain" in self.api.param_spec(operation_id, "path", required=True):
                parameters["pulp_domain"] = self.pulp_domain
        parameters = preprocess_payload(parameters)
        if body is not None:
            body = preprocess_payload(body)
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
            if e.response is not None:
                raise PulpHTTPError(str(e.response.text), e.response.status_code)
            else:
                raise PulpException(str(e))
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

    @staticmethod
    def _task_finished(task: EntityDefinition, expect_cancel: bool = False) -> bool:
        task_href = task["pulp_href"]

        if task["state"] == "completed":
            if expect_cancel:
                raise PulpException(
                    _("The task {task_href} meant to be canceled, completed instead.")
                )
            return True
        elif task["state"] == "failed":
            raise PulpException(
                _("Task {task_href} failed: '{description}'").format(
                    task_href=task_href,
                    description=task["error"].get("description") or task["error"].get("reason"),
                )
            )
        elif task["state"] == "canceled":
            if expect_cancel:
                return True
            raise PulpException(_("Task {task_href} canceled").format(task_href=task_href))
        elif task["state"] in ["waiting", "running", "canceling"]:
            return False
        else:
            raise NotImplementedError(_("Unknown task state: {state}").format(state=task["state"]))

    def wait_for_task(self, task: EntityDefinition, expect_cancel: bool = False) -> Any:
        """
        Wait for a task to finish and return the finished task object.

        Parameters:
            task: A task object to monitor.
            expect_cancel: Swaps the raising condition for completed and canceled tasks.

        Raises:
            PulpNoWait: on timeout or if the context has `background_tasks` set.
            PulpException: on ctrl-c, if task failed or was canceled.
        """
        deadline = datetime.datetime.now() + self.timeout if self.timeout else None

        if self.background_tasks:
            raise PulpNoWait(_("Not waiting for task because --background was specified."))
        task_href = task["pulp_href"]
        try:
            while not self._task_finished(task, expect_cancel=expect_cancel):
                if deadline and datetime.datetime.now() > deadline:
                    raise PulpNoWait(
                        _("Waiting for task {task_href} timed out.").format(
                            task_href=task["pulp_href"]
                        )
                    )
                time.sleep(1)
                self.echo(".", nl=False, err=True)
                task = self.api.call("tasks_read", parameters={"task_href": task["pulp_href"]})
            self.echo("Done.", err=True)
            return task
        except KeyboardInterrupt:
            raise PulpNoWait(_("Task {task_href} sent to background.").format(task_href=task_href))

    def _task_group_finished(self, task_group: EntityDefinition) -> bool:
        if task_group["waiting"] + task_group["running"] + task_group["canceling"] > 0:
            return False
        if task_group["failed"] + task_group["canceled"] > 0:
            errors = []
            for task in task_group["tasks"]:
                if task["state"] in ["failed", "canceled"]:
                    task = self.api.call("tasks_read", parameters={"task_href": task["pulp_href"]})
                    errors.append(task["error"].get("description") or task["error"].get("reason"))
            raise PulpException(
                _("Task group {task_group_href} has failed/canceled tasks: '{errors}'").format(
                    task_group_href=task_group["pulp_href"],
                    errors="\n".join(errors),
                )
            )
        return True

    def wait_for_task_group(self, task_group: EntityDefinition) -> Any:
        """
        Wait for a task group to finish and return the finished task object.

        Parameters:
            task_group: A task group object all of which's tasks to monitor.

        Raises:
            PulpNoWait: on timeout or if the context has `background_tasks` set.
            PulpException: on ctrl-c, if task failed or was canceled.
        """
        deadline = datetime.datetime.now() + self.timeout if self.timeout else None

        if self.background_tasks:
            raise PulpNoWait("Not waiting for task group because --background was specified.")
        try:
            while not self._task_group_finished(task_group):
                if deadline and datetime.datetime.now() > deadline:
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
        plugin_requirement: PluginRequirement,
    ) -> bool:
        version: Optional[str] = self.component_versions.get(plugin_requirement.name)
        return version in plugin_requirement

    def needs_plugin(
        self,
        plugin_requirement: PluginRequirement,
    ) -> None:
        if self._api is not None:
            if not self.has_plugin(plugin_requirement):
                component = f"{plugin_requirement.name}{plugin_requirement.specifier}"
                feature = plugin_requirement.feature or _("this command")
                if plugin_requirement.inverted:
                    msg = _(
                        "The server provides the pulp component '{component}',"
                        " which prevents the use of {feature}."
                        " See 'pulp status' for installed components."
                    )
                else:
                    msg = _(
                        "The server does not provide the pulp component '{component}',"
                        " which is needed to use {feature}."
                        " See 'pulp status' for installed components."
                    )
                raise PulpException(msg.format(component=component, feature=feature))
        else:
            # Schedule for later checking
            self._needed_plugins.append(plugin_requirement)


class PulpEntityContext:
    """
    Base class for entity specific contexts.
    This class provides the basic CRUD commands and ties its instances to the global
    PulpContext for api access.
    Mostly specification is achieved by defining / extending the class attributes below.

    Parameters:
        pulp_ctx: The server context to attach this entity to.
        pulp_href: Specifying this is equivalent to assinging to `pulp_href` later.
        entity: Specifying this is equivalent to assinging to `entity` later.
    """

    # Subclasses should provide appropriate values here
    ENTITY: ClassVar[str] = _("entity")
    """Translatable name of the entity."""
    ENTITIES: ClassVar[str] = _("entities")
    """Translatable plural of `ENTITY`."""
    HREF: ClassVar[str]
    """Name of the href parameter in the url patterns."""
    ID_PREFIX: ClassVar[str]
    """Common prefix for the operations of this entity."""
    NULLABLES: ClassVar[Set[str]] = set()
    """Set of fields that can be cleared by sending 'null'."""
    NEEDS_PLUGINS: ClassVar[List[PluginRequirement]] = []
    """List of plugin requirements to operate such an entity on the server."""
    CAPABILITIES: ClassVar[Dict[str, List[PluginRequirement]]] = {}
    """
    List of capabilities this entity provides.

    Subclasses can specify version dependent capabilities here

    Example:
        ```
        CAPABILITIES = {
            "feature1": [
                PluginRequirement("file"),
                PluginRequirement("core", specifier=">=3.7.0")
            ]
        }
        ```
    """
    HREF_PATTERN: str
    """Regular expression with capture groups for 'plugin' and 'resource_type' to match URIs."""

    # Hidden values for the lazy entity lookup
    _entity: Optional[EntityDefinition]
    _entity_lookup: EntityDefinition

    @property
    def scope(self) -> Dict[str, Any]:
        """
        Extra scope used in parameters for create and list calls.

        Subclasses for nested entities can define the parameters for there parent scope here.
        """
        return {}

    @property
    def entity(self) -> EntityDefinition:
        """
        Entity property that will perform a lazy lookup once it is accessed.
        You can specify lookup parameters by assigning a dictionary to it,
        or assign an href to the `pulp_href` property.
        To reset to having no attached entity you can assign `None`.
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

    @property
    def tangible(self) -> bool:
        """Indicate whether an entity is available or specified by search parameters."""
        return bool(self._entity) or bool(self._entity_lookup)

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
        for plugin_requirement in self.NEEDS_PLUGINS:
            self.pulp_ctx.needs_plugin(plugin_requirement)

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
        validate_body: bool = True,
    ) -> Any:
        """
        Perform an API call for operation.
        Wait for triggered tasks to finish if not background.
        Returns the operation result, or the finished task.

        Parameters:
            operation: The operation to be performed on the entity. Usually the openapi
                operation_id is constructed by concatenating with the `ID_PREFIX`.
            non_blocking: returns unfinished tasks if `True`.
            parameters: Arguments that are to be sent as headers, querystrings or part of the URI.
            body: Body payload for POST, PUT, PATCH calls.
            validate_body: Indicate whether the body should be validated.

        Returns:
            The body of the response, or the task or task group if one was issued.

        Raises:
            PulpNoWait: in case the context has `background_tasks` set or a task (group) timed out.
        """
        operation_id: str = (
            getattr(self, operation.upper() + "_ID", None) or self.ID_PREFIX + "_" + operation
        )
        return self.pulp_ctx.call(
            operation_id,
            non_blocking=non_blocking,
            parameters=parameters,
            body=body,
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
        """
        Filter to prepare the body for a create or update call.

        This function can be subclassed by specific Entity contexts to fix data depending on plugin
        versions.

        Parameters:
            body: The payload representing the entity to create or the fields to update on it.
            partial: Should be set if `body` may only represent part of the entity.

        Returns:
            The body ready to be passed to `call`.
        """
        return self.preprocess_body(body)

    def list(self, limit: int, offset: int, parameters: Dict[str, Any]) -> List[Any]:
        """
        List entities by the type of this context.

        Parameters:
            limit: Maximal number of entities to return.
            offset: Number of entities to skip at the front of the list.
            parameters: Additional search or sorting criteria.

        Returns:
            List of entities matching the conditions.
        """
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
        """
        Find an entity based on search parameters.

        Note: It is preferred to use the `entity` property instead of calling `find` directly.

        Parameters:
            kwargs: The search parameters.

        Returns:
            The entity if one was found uniquely.

        Raises:
            PulpException: if no entity satisfies the search parameters uniquely.
        """
        search_result = self.list(limit=1, offset=0, parameters=kwargs)
        if len(search_result) != 1:
            raise PulpException(
                _("Could not find {entity} with {kwargs}.").format(
                    entity=self.ENTITY, kwargs=kwargs
                )
            )
        return search_result[0]

    def show(self, href: Optional[str] = None) -> Any:
        """
        Retrieve and return the full record of an entity from the server.

        Parameters:
            href: href of the entity to fetch. If not specified, the entity represented by `entity`
                will be used.

        Returns:
            The full record of the entity as reported by the server.

        Raises:
            PulpException: if no href was specified and the lazy lookup failed.
        """
        return self.call("read", parameters={self.HREF: href or self.pulp_href})

    def create(
        self,
        body: EntityDefinition,
        parameters: Optional[Mapping[str, Any]] = None,
        non_blocking: bool = False,
    ) -> Any:
        """
        Create an entity.

        Parameters:
            body: Fields off the new entity and the values they should be set to.
            parameters: Additional parameters for the call (usually not needed).
            non_blocking: Whether the result of the operation should be awaited on.

        Returns:
            The created entity, or the record of the create task if non_blocking.
        """
        _parameters = self.scope
        if parameters:
            _parameters.update(parameters)
        if body is not None:
            body = self.preprocess_entity(body, partial=False)
        result = self.call(
            "create",
            parameters=_parameters,
            body=body,
            non_blocking=non_blocking,
        )
        if result["pulp_href"].startswith(self.pulp_ctx.api_path + "tasks/"):
            if not non_blocking:
                self.pulp_href = result["created_resources"][0]
                result = self.entity
        else:
            self._entity = result

        return result

    def update(
        self,
        href: Optional[str] = None,
        body: Optional[EntityDefinition] = None,
        parameters: Optional[Mapping[str, Any]] = None,
        non_blocking: bool = False,
    ) -> Any:
        """
        Update the entity.

        Parameters:
            body: Fields and the values they should be changed to.
            parameters: Additional parameters for the call (usually not needed).
            non_blocking: Whether the result of the operation should be awaited on.
            href: **[DEPRECATED]**

        Returns:
            The updated entity, or the record of the update task if non_blocking.
        """
        _parameters = {self.HREF: href or self.pulp_href}
        if parameters:
            _parameters.update(parameters)
        if body is not None:
            body = self.preprocess_entity(body, partial=False)
        result = self.call(
            "partial_update",
            parameters=_parameters,
            body=body,
            non_blocking=non_blocking,
        )
        if result["pulp_href"].startswith(self.pulp_ctx.api_path + "tasks/"):
            if not non_blocking:
                self.pulp_href = self.pulp_href  # reload from server
                result = self.entity
        else:
            self._entity = result

        return result

    def delete(self, href: Optional[str] = None, non_blocking: bool = False) -> Any:
        """
        Delete the entity.

        Parameters:
            non_blocking: Whether the result of the operation should be awaited on.
            href: **[DEPRECATED]**

        Returns:
            The record of the delete task.
        """
        return self.call(
            "delete", parameters={self.HREF: href or self.pulp_href}, non_blocking=non_blocking
        )

    def set_label(self, key: str, value: str, non_blocking: bool = False) -> Any:
        """
        Set a label.

        Parameters:
            key: Name of the label.
            value: Value of the label.
            non_blocking: Whether the result of the operation should be awaited on.
                This no longer relevant for pulpcore>=3.34, because the synchronous api is used.
        """
        if self.pulp_ctx.has_plugin(PluginRequirement("core", specifier=">=3.34.0")):
            try:
                return self.call(
                    "set_label",
                    parameters={self.HREF: self.pulp_href},
                    body={"key": key, "value": value},
                )
            except PulpHTTPError as e:
                if e.status_code != 403:
                    raise
                # Workaround for broken access policies: Try the old mechanism.
        labels = self.entity["pulp_labels"]
        labels[key] = value
        return self.update(body={"pulp_labels": labels}, non_blocking=non_blocking)

    def unset_label(self, key: str, non_blocking: bool = False) -> Any:
        """
        Unset a label.

        Parameters:
            key: Name of the label.
            non_blocking: Whether the result of the operation should be awaited on.
                This no longer relevant for pulpcore>=3.34, because the synchronous api is used.
        """
        if self.pulp_ctx.has_plugin(PluginRequirement("core", specifier=">=3.34.0")):
            try:
                return self.call(
                    "unset_label", parameters={self.HREF: self.pulp_href}, body={"key": key}
                )
            except PulpHTTPError as e:
                if e.status_code != 403:
                    raise
                # Workaround for broken access policies: Try the old mechanism.
        labels = self.entity["pulp_labels"]
        try:
            labels.pop(key)
        except KeyError:
            raise PulpException(_("Could not find label with key '{key}'.").format(key=key))
        return self.update(body={"pulp_labels": labels}, non_blocking=non_blocking)

    def show_label(self, key: str) -> t.Optional[str]:
        """
        Show value of a label.

        Parameters:
            key: Name of the label.

        Returns:
            Value of the label or None.

        Raises:
            PulpException: if the label was not set.
        """
        labels: t.Dict[str, t.Optional[str]] = self.entity["pulp_labels"]
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
        """
        Report on a capability based on the presence of all needed server plugins.

        Parameters:
            capability: Name of a capability.

        Returns:
            Whether the capability is provided for this context.
        """
        return capability in self.CAPABILITIES and all(
            (self.pulp_ctx.has_plugin(pr) for pr in self.CAPABILITIES[capability])
        )

    def needs_capability(self, capability: str) -> None:
        """
        Translates a capability in calls to `needs_plugin` via `CAPABILITIES`.

        Parameters:
            capability: Name of a capability.
        """
        if capability in self.CAPABILITIES:
            for plugin_requirement in self.CAPABILITIES[capability]:
                self.pulp_ctx.needs_plugin(plugin_requirement)
        else:
            raise PulpException(
                _("Capability '{capability}' needed on '{entity}' for this command.").format(
                    capability=capability, entity=self.ENTITY
                )
            )


class PulpRemoteContext(PulpEntityContext):
    """
    Base class for remote contexts.
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
    TYPE_REGISTRY: Dict[str, Type["PulpRemoteContext"]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "PLUGIN") and hasattr(cls, "RESOURCE_TYPE"):
            cls.TYPE_REGISTRY[f"{cls.PLUGIN}:{cls.RESOURCE_TYPE}"] = cls


class PulpPublicationContext(PulpEntityContext):
    """Base class for publication contexts."""

    ENTITY = _("publication")
    ENTITIES = _("publications")
    ID_PREFIX = "publications"
    HREF_PATTERN = r"publications/(?P<plugin>[\w\-_]+)/(?P<resource_type>[\w\-_]+)/"
    TYPE_REGISTRY: Dict[str, Type["PulpPublicationContext"]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "PLUGIN") and hasattr(cls, "RESOURCE_TYPE"):
            cls.TYPE_REGISTRY[f"{cls.PLUGIN}:{cls.RESOURCE_TYPE}"] = cls

    def list(self, limit: int, offset: int, parameters: Dict[str, Any]) -> List[Any]:
        if parameters.get("repository") is not None:
            self.pulp_ctx.needs_plugin(
                PluginRequirement("core", specifier=">=3.20.0", feature=_("repository filter"))
            )
        return super().list(limit, offset, parameters)


class PulpDistributionContext(PulpEntityContext):
    """Base class for distribution contexts."""

    ENTITY = _("distribution")
    ENTITIES = _("distributions")
    ID_PREFIX = "distributions"
    HREF_PATTERN = r"distributions/(?P<plugin>[\w\-_]+)/(?P<resource_type>[\w\-_]+)/"
    NULLABLES = {"content_guard", "publication", "remote", "repository", "repository_version"}
    TYPE_REGISTRY: Dict[str, Type["PulpDistributionContext"]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "PLUGIN") and hasattr(cls, "RESOURCE_TYPE"):
            cls.TYPE_REGISTRY[f"{cls.PLUGIN}:{cls.RESOURCE_TYPE}"] = cls


class PulpRepositoryVersionContext(PulpEntityContext):
    """
    Base class for repository version contexts.

    Parameters:
        pulp_ctx: The server context to attach this entity to.
        repository_ctx: Context of the repository this context should be scoped to.
        pulp_href: Specifying this is equivalent to assinging to `pulp_href` later.
    """

    ENTITY = _("repository version")
    ENTITIES = _("repository versions")
    ID_PREFIX = "repository_versions"
    repository_ctx: "PulpRepositoryContext"

    def __init__(
        self,
        pulp_ctx: PulpContext,
        repository_ctx: "PulpRepositoryContext",
        pulp_href: Optional[str] = None,
    ) -> None:
        super().__init__(pulp_ctx, pulp_href=pulp_href)
        self.repository_ctx = repository_ctx

    @property
    def scope(self) -> Dict[str, Any]:
        if self.ID_PREFIX == "repository_versions":
            return {}
        else:
            return {self.repository_ctx.HREF: self.repository_ctx.pulp_href}

    def repair(self, href: Optional[str] = None) -> Any:
        """
        Trigger a repair task for this repository version.

        Parameters:
            href: **[DEPRECATED]**

        Returns:
            The record of the repair task.
        """
        return self.call("repair", parameters={self.HREF: href or self.pulp_href}, body={})


class PulpRepositoryContext(PulpEntityContext):
    """Base class for repository contexts."""

    ENTITY = _("repository")
    ENTITIES = _("repositories")
    HREF_PATTERN = r"repositories/(?P<plugin>[\w\-_]+)/(?P<resource_type>[\w\-_]+)/"
    ID_PREFIX = "repositories"
    VERSION_CONTEXT: ClassVar[Type[PulpRepositoryVersionContext]] = PulpRepositoryVersionContext
    NULLABLES = {"description", "retain_repo_versions"}
    TYPE_REGISTRY: Dict[str, Type["PulpRepositoryContext"]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "PLUGIN") and hasattr(cls, "RESOURCE_TYPE"):
            cls.TYPE_REGISTRY[f"{cls.PLUGIN}:{cls.RESOURCE_TYPE}"] = cls

    def get_version_context(
        self,
        number: Optional[int] = None,
    ) -> PulpRepositoryVersionContext:
        """
        Return a repository version context of the proper type scoped for this repository.

        Parameters:
            number: Version number or `-1` for the latest version.

        Returns:
            Repository version context attached to the same pulp_ctx and scoped to the repository.
        """
        if number is not None:
            if number >= 0:
                version_href = self.entity["versions_href"] + f"{number}/"
            elif number == -1:
                version_href = self.entity["latest_version_href"]
            else:
                PulpException(_("Invalid version number ({number}).").format(number=number))
        else:
            version_href = None
        return self.VERSION_CONTEXT(
            pulp_ctx=self.pulp_ctx, repository_ctx=self, pulp_href=version_href
        )

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if "retain_repo_versions" in body:
            self.pulp_ctx.needs_plugin(PluginRequirement("core", specifier=">=3.13.0"))
        if self.pulp_ctx.has_plugin(PluginRequirement("core", specifier=">=3.13.0,<3.15.0")):
            # "retain_repo_versions" has been named "retained_versions" until pulpcore 3.15
            # https://github.com/pulp/pulpcore/pull/1472
            if "retain_repo_versions" in body:
                body["retained_versions"] = body.pop("retain_repo_versions")
        return body

    def sync(self, href: Optional[str] = None, body: Optional[EntityDefinition] = None) -> Any:
        """
        Trigger a sync task for this repository.

        Parameters:
            body: Any additional options specific to the repository type used to perform this sync.
            href: [DEPRECATED]

        Returns:
            Record of the sync task.
        """
        return self.call("sync", parameters={self.HREF: href or self.pulp_href}, body=body or {})

    def modify(
        self,
        href: Optional[str] = None,
        add_content: Optional[List[str]] = None,
        remove_content: Optional[List[str]] = None,
        base_version: Optional[str] = None,
    ) -> Any:
        """
        Add to or remove content from this repository.

        Parameters:
            add_content: List of content hrefs to add.
            remove_content: List of content hrefs to remove.
            base_version: Href to a repository version relative to whose content the changes are to
                be interpreted.
            href: [DEPRECATED]

        Returns:
            Record of the modify task.
        """
        body: Dict[str, Any] = {}
        if add_content is not None:
            body["add_content_units"] = add_content
        if remove_content is not None:
            body["remove_content_units"] = remove_content
        if base_version is not None:
            body["base_version"] = base_version
        return self.call("modify", parameters={self.HREF: href or self.pulp_href}, body=body)


class PulpGenericRepositoryContext(PulpRepositoryContext):
    """Generic repository context class to separate specific general functionality."""

    def reclaim(
        self,
        repo_hrefs: List[t.Union[str, PulpRepositoryContext]],
        repo_versions_keeplist: Optional[List[t.Union[str, PulpRepositoryVersionContext]]] = None,
    ) -> Any:
        """
        Reclaim disk space for a list of repositories.

        Parameters:
            repo_hrefs: List of repository hrefs to reclaim.
            repo_versions_keeplist: List of repository version hrefs to keep unaffected.

        Returns:
            Record of the reclaim space task.
        """
        self.pulp_ctx.needs_plugin(PluginRequirement("core", specifier=">=3.19.0"))
        body: Dict[str, Any] = {}
        body["repo_hrefs"] = repo_hrefs
        if repo_versions_keeplist:
            body["repo_versions_keeplist"] = repo_versions_keeplist
        return self.call("reclaim_space_reclaim", body=body)


class PulpContentContext(PulpEntityContext):
    """Base class for content contexts."""

    ENTITY = _("content")
    ENTITIES = _("content")
    ID_PREFIX = "content"
    TYPE_REGISTRY: Dict[str, Type["PulpContentContext"]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "PLUGIN") and hasattr(cls, "RESOURCE_TYPE"):
            cls.TYPE_REGISTRY[f"{cls.PLUGIN}:{cls.RESOURCE_TYPE}"] = cls

    def upload(
        self,
        file: IO[bytes],
        chunk_size: int,
        repository: Optional[PulpRepositoryContext],
        **kwargs: Any,
    ) -> Any:
        """
        Create a content unit by uploading a file.

        Parameters:
            file: A file like object that supports `os.path.getsize`.
            chunk_size: Size of the chunks to upload independently.
            repository: Repository context to add the newly created content to.
            kwargs: Extra args specific to the content type, passed to the create call.

        Returns:
            The result of the create task.
        """
        self.needs_capability("upload")
        size = os.path.getsize(file.name)
        body: Dict[str, Any] = {**kwargs}
        if chunk_size > size:
            body["file"] = file
        elif self.pulp_ctx.has_plugin(PluginRequirement("core", specifier=">=3.20.0")):
            from pulp_glue.core.context import PulpUploadContext

            upload_href = PulpUploadContext(self.pulp_ctx).upload_file(file, chunk_size)
            body["upload"] = upload_href
        else:
            from pulp_glue.core.context import PulpArtifactContext

            artifact_href = PulpArtifactContext(self.pulp_ctx).upload(file, chunk_size)
            body["artifact"] = artifact_href
        if repository:
            body["repository"] = repository
        return self.create(body=body)


class PulpACSContext(PulpEntityContext):
    """Base class for ACS contexts."""

    ENTITY = _("ACS")
    ENTITIES = _("ACSes")
    HREF_PATTERN = r"acs/(?P<plugin>[\w\-_]+)/(?P<resource_type>[\w\-_]+)/"
    ID_PREFIX = "acs"
    TYPE_REGISTRY: Dict[str, Type["PulpACSContext"]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "PLUGIN") and hasattr(cls, "RESOURCE_TYPE"):
            cls.TYPE_REGISTRY[f"{cls.PLUGIN}:{cls.RESOURCE_TYPE}"] = cls

    def refresh(self, href: Optional[str] = None) -> Any:
        return self.call("refresh", parameters={self.HREF: href or self.pulp_href})


class PulpContentGuardContext(PulpEntityContext):
    """Base class for content guard contexts."""

    ENTITY = "content guard"
    ENTITIES = "content guards"
    ID_PREFIX = "contentguards"
    HREF_PATTERN = r"contentguards/(?P<plugin>[\w\-_]+)/(?P<resource_type>[\w\-_]+)/"
    NULLABLES = {"description"}
    TYPE_REGISTRY: Dict[str, Type["PulpContentGuardContext"]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "PLUGIN") and hasattr(cls, "RESOURCE_TYPE"):
            cls.TYPE_REGISTRY[f"{cls.PLUGIN}:{cls.RESOURCE_TYPE}"] = cls


EntityFieldDefinition = Union[None, str, PulpEntityContext]


##############################################################################
# Registries for Contexts of different sorts
# A command can use these to identify e.g. all repository types known to the CLI
# Note that it will only be fully populated, once all plugins are loaded.
# This is deprecated. Please specify PLUGIN and RESOURCE_TYPE on the context instead.

registered_repository_contexts: Dict[
    str, Type[PulpRepositoryContext]
] = PulpRepositoryContext.TYPE_REGISTRY
