from typing import Any, Optional, Dict, List, Tuple

import click
import datetime
import json
import os
import time

import toml
import yaml

from requests import HTTPError

from pulpcore.cli.openapi import OpenAPI, OpenAPIError

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

    def __init__(self, api: OpenAPI, format: str, background_tasks: bool) -> None:
        self.api: OpenAPI = api
        self.format: str = format
        self.background_tasks: bool = background_tasks

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
            raise click.ClickException(str(e.response.json()))
        if "task" in result:
            task_href = result["task"]
            result = self.api.call("tasks_read", parameters={"task_href": task_href})
            click.echo(f"Started background task {task_href}", err=True)
            if not self.background_tasks:
                result = self.wait_for_task(result)
        return result

    def wait_for_task(self, task: Dict[str, Any], timeout: int = 120) -> Any:
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


class PulpEntityContext:
    """
    Base class for entity specific contexts.
    This class provides the basic CRUD commands and ties its instances to the global
    PulpContext for api access.
    """

    # Subclasses should provide appropriate values here
    ENTITY: str
    HREF: str
    LIST_ID: str
    READ_ID: str
    CREATE_ID: str
    UPDATE_ID: str
    DELETE_ID: str
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

    entity: Dict[str, Any]

    def __init__(self, pulp_ctx: PulpContext) -> None:
        self.pulp_ctx: PulpContext = pulp_ctx

    def list(self, limit: int, offset: int, parameters: Dict[str, Any]) -> List[Any]:
        count: int = -1
        entities: List[Any] = []
        payload: Dict[str, Any] = parameters.copy()
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

    def create(self, body: Dict[str, Any]) -> Any:
        return self.pulp_ctx.call(self.CREATE_ID, body=body)

    def update(self, href: str, body: Dict[str, Any]) -> Any:
        return self.pulp_ctx.call(self.UPDATE_ID, parameters={self.HREF: href}, body=body)

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


class PulpRepositoryContext(PulpEntityContext):
    """
    Base class for repository specific contexts.
    This class provides the basic CRUD commands as well as synchronizing and
    ties its instances to the global PulpContext for api access.
    """

    ENTITY = "repository"
    SYNC_ID: str

    def sync(self, href: str, body: Dict[str, Any]) -> Any:
        return self.pulp_ctx.call(
            self.SYNC_ID,
            parameters={self.HREF: href},
            body=body,
        )


##############################################################################
# Decorator to access certain contexts or for common options


pass_pulp_context = click.make_pass_decorator(PulpContext)
pass_entity_context = click.make_pass_decorator(PulpEntityContext)
pass_repository_context = click.make_pass_decorator(PulpRepositoryContext)

limit_option = click.option(
    "--limit", default=DEFAULT_LIMIT, type=int, help="Limit the number of entries to show."
)
offset_option = click.option(
    "--offset", default=0, type=int, help="Skip a number of entries to show."
)


##############################################################################
# Generic reusable commands


@click.command(name="list")
@limit_option
@offset_option
@pass_entity_context
@pass_pulp_context
def list_entities(
    pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, limit: int, offset: int, **kwargs: Any
) -> None:
    """
    Show a list of entries
    """
    parameters = {k: v for k, v in kwargs.items() if v is not None}
    result = entity_ctx.list(limit=limit, offset=offset, parameters=parameters)
    pulp_ctx.output_result(result)


@click.command(name="show")
@click.option("--name", required=True, help="Name of the entry")
@pass_entity_context
@pass_pulp_context
def show_by_name(pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, name: str) -> None:
    """Shows details of an entry"""
    href = entity_ctx.find(name=name)["pulp_href"]
    entity = entity_ctx.show(href)
    pulp_ctx.output_result(entity)


@click.command(name="show")
@click.option("--href", required=True, help="HREF of the entry")
@pass_entity_context
@pass_pulp_context
def show_by_href(pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, href: str) -> None:
    """Shows details of an entry"""
    entity = entity_ctx.show(href)
    pulp_ctx.output_result(entity)


@click.command(name="destroy")
@click.option("--name", required=True, help="Name of the entry to destroy")
@pass_entity_context
def destroy_by_name(entity_ctx: PulpEntityContext, name: str) -> None:
    """
    Destroy an entry
    """
    href = entity_ctx.find(name=name)["pulp_href"]
    entity_ctx.delete(href)


@click.command(name="destroy")
@click.option("--href", required=True, help="HREF of the entry to destroy")
@pass_entity_context
def destroy_by_href(entity_ctx: PulpEntityContext, href: str) -> None:
    """
    Destroy an entry
    """
    entity_ctx.delete(href)


##############################################################################
# Main entry point


def _config_callback(ctx: click.Context, param: Any, value: str) -> None:
    if ctx.default_map:
        return

    if value:
        ctx.default_map = toml.load(value)["cli"]
    else:
        xdg_config_home = os.path.expanduser(os.environ.get("XDG_CONFIG_HOME") or "~/.config")
        default_config_path = os.path.join(xdg_config_home, "pulp", "settings.toml")

        try:
            ctx.default_map = toml.load(default_config_path)["cli"]
        except FileNotFoundError:
            pass


@click.group()
@click.version_option(prog_name="pulp3 command line interface")
@click.option(
    "--config",
    type=click.Path(resolve_path=True),
    help="Path to the Pulp settings.toml file",
    callback=_config_callback,
    expose_value=False,
)
@click.option("--base-url", default="https://localhost", help="Api base url")
@click.option("--user", help="Username on pulp server")
@click.option("--password", help="Password on pulp server")
@click.option("--verify-ssl/--no-verify-ssl", default=True, help="Verify SSL connection")
@click.option(
    "--format", type=click.Choice(["json", "yaml", "none"], case_sensitive=False), default="json"
)
@click.option(
    "-v",
    "--verbose",
    type=int,
    count=True,
    help="Increase verbosity; explain api calls as they are made",
)
@click.option(
    "-b",
    "--background",
    is_flag=True,
    help="Start tasks in the background instead of awaiting them",
)
@click.pass_context
def main(
    ctx: click.Context,
    base_url: str,
    user: Optional[str],
    password: Optional[str],
    verify_ssl: bool,
    format: str,
    verbose: int,
    background: bool,
) -> None:
    if user and not password:
        password = click.prompt("password", hide_input=True)
    try:
        api = OpenAPI(
            base_url=base_url,
            doc_path="/pulp/api/v3/docs/api.json",
            username=user,
            password=password,
            validate_certs=verify_ssl,
            refresh_cache=True,
            debug_callback=lambda level, x: click.secho(x, err=True, bold=True)
            if verbose >= level
            else None,
        )
    except OpenAPIError as e:
        raise click.ClickException(str(e))
    ctx.obj = PulpContext(api=api, format=format, background_tasks=background)
