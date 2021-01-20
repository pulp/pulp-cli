from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type

import click
import datetime
import json
import time
import yaml

from packaging.version import parse as parse_version
from requests import HTTPError

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


DEFAULT_LIMIT = 25
BATCH_SIZE = 25


EntityDefinition = Dict[str, Any]
RepositoryDefinition = Tuple[str, str]  # name, pulp_type
RepositoryVersionDefinition = Tuple[str, str, int]  # name, pulp_type, version


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
        self._needed_plugins: List[Tuple[str, Optional[str], Optional[str]]] = []

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
            for name, min_version, max_version in self._needed_plugins:
                self.needs_plugin(name, min_version, max_version)
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
            output = json.dumps(result, cls=PulpJSONEncoder, indent=2)
            if PYGMENTS:
                output = highlight(output, JsonLexer(), Terminal256Formatter(style=PYGMENTS_STYLE))
            click.echo(output)
        elif self.format == "yaml":
            output = yaml.dump(result)
            if PYGMENTS:
                output = highlight(output, YamlLexer(), Terminal256Formatter(style=PYGMENTS_STYLE))
            click.echo(output)
        elif self.format == "none":
            pass
        else:
            raise NotImplementedError(f"Format '{self.format}' not implemented.")

    def call(self, operation_id: str, *args: Any, **kwargs: Any) -> Any:
        """
        Perform an API call for operation_id.
        Wait for triggered tasks to finish if not background.
        """
        try:
            result = self.api.call(operation_id, *args, **kwargs)
        except OpenAPIError as e:
            raise click.ClickException(str(e))
        except HTTPError as e:
            raise click.ClickException(str(e.response.text))
        if "task" in result:
            task_href = result["task"]
            result = self.api.call("tasks_read", parameters={"task_href": task_href})
            click.echo(f"Started background task {task_href}", err=True)
            if not self.background_tasks:
                result = self.wait_for_task(result)
        return result

    def wait_for_task(self, task: EntityDefinition, timeout: int = 120) -> Any:
        """
        Wait for a task to finish and return the finished task object.
        """
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
            click.echo(f"Task {task_href} sent to background.", err=True)
            return task

    def has_plugin(
        self, name: str, min_version: Optional[str] = None, max_version: Optional[str] = None
    ) -> bool:
        if not self.component_versions:
            # Prior to 3.9 we do not have this information
            # assume yes if no version constraint is specified
            return (min_version is None) and (max_version is None)
        version: Optional[str] = self.component_versions.get(name)
        if version is None:
            return False
        if min_version is not None:
            if parse_version(version) < parse_version(min_version):
                return False
        if max_version is not None:
            if parse_version(version) >= parse_version(max_version):
                return False
        return True

    def needs_plugin(
        self, name: str, min_version: Optional[str] = None, max_version: Optional[str] = None
    ) -> None:
        if self._api is not None:
            if not self.has_plugin(name, min_version, max_version):
                specifier = name
                separator = ""
                if min_version is not None:
                    specifier += f">={min_version}"
                    separator = ","
                if max_version is not None:
                    specifier += f"{separator}<{max_version}"
                raise click.ClickException(f"'{specifier} is not available")
        else:
            # Schedule for later checking
            self._needed_plugins.append((name, min_version, max_version))


class PulpEntityContext:
    """
    Base class for entity specific contexts.
    This class provides the basic CRUD commands and ties its instances to the global
    PulpContext for api access.
    """

    # Subclasses should provide appropriate values here
    ENTITY: ClassVar[str]
    HREF: ClassVar[str]
    LIST_ID: ClassVar[str]
    READ_ID: ClassVar[str]
    CREATE_ID: ClassVar[str]
    UPDATE_ID: ClassVar[str]
    DELETE_ID: ClassVar[str]

    _entity: Optional[EntityDefinition]
    _entity_lookup: Optional[EntityDefinition]

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
            if self._entity_lookup is None:
                raise click.ClickException(f"A {self.ENTITY} must be specified for this command.")
            if "pulp_href" in self._entity_lookup:
                self._entity = self.show(self._entity_lookup["pulp_href"])
            else:
                self._entity = self.find(**self._entity_lookup)
        return self._entity

    @entity.setter
    def entity(self, value: Optional[EntityDefinition]) -> None:
        # Setting this property will always (lazily) retrigger retrieving the entity
        self._entity_lookup = value
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
        # Setting this property will always (lazily) retrigger retrieving the entity
        self._entity_lookup = {"pulp_href": value}
        self._entity = None

    def __init__(
        self,
        pulp_ctx: PulpContext,
        pulp_href: Optional[str] = None,
        entity: Optional[EntityDefinition] = None,
    ) -> None:
        assert pulp_href is None or entity is None

        self.pulp_ctx: PulpContext = pulp_ctx
        self._entity = None
        if pulp_href is None:
            self._entity_lookup = entity
        else:
            self.pulp_href = pulp_href

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

    def create(self, body: EntityDefinition, parameters: Optional[Dict[str, Any]] = None) -> Any:
        _parameters = self.scope
        if parameters:
            _parameters.update(parameters)
        return self.pulp_ctx.call(self.CREATE_ID, parameters=parameters, body=body)

    def update(
        self,
        href: str,
        body: EntityDefinition,
        parameters: Optional[Dict[str, Any]] = None,
        uploads: Optional[Dict[str, Any]] = None,
    ) -> Any:
        _parameters = {self.HREF: href}
        if parameters:
            _parameters.update(parameters)
        return self.pulp_ctx.call(
            self.UPDATE_ID, parameters=_parameters, body=body, uploads=uploads
        )

    def delete(self, href: str) -> Any:
        return self.pulp_ctx.call(self.DELETE_ID, parameters={self.HREF: href})

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


class PulpRepositoryVersionContext(PulpEntityContext):
    """
    Base class for repository version specific contexts.
    This class provides the basic CRUD commands and
    ties its instances to the global PulpContext for api access.
    """

    ENTITY = "repository version"
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
    SYNC_ID: ClassVar[str]
    MODIFY_ID: ClassVar[str]
    VERSION_CONTEXT: ClassVar[Type[PulpRepositoryVersionContext]]

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


##############################################################################
# Decorator to access certain contexts


pass_pulp_context = click.make_pass_decorator(PulpContext)
pass_entity_context = click.make_pass_decorator(PulpEntityContext)
pass_repository_context = click.make_pass_decorator(PulpRepositoryContext)
pass_repository_version_context = click.make_pass_decorator(PulpRepositoryVersionContext)
