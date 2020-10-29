from typing import Any, Optional, Dict, List

import click
import datetime
import json
import os
import time

import toml
import yaml

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


limit_option = click.option(
    "--limit", default=DEFAULT_LIMIT, type=int, help="Limit the number of entries to show."
)
offset_option = click.option(
    "--offset", default=0, type=int, help="Skip a number of entries to show."
)


class PulpJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return super().default(obj)


class PulpContext:
    def __init__(self, api: OpenAPI, format: str) -> None:
        self.api: OpenAPI = api
        self.format: str = format

    def output_result(self, result: Any) -> None:
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

    def call(self, operation_id: str, background: bool = False, *args: Any, **kwargs: Any) -> Any:
        try:
            result = self.api.call(operation_id, *args, **kwargs)
        except OpenAPIError as e:
            raise click.ClickException(str(e))
        if "task" in result:
            task_href = result["task"]
            click.echo(f"Started task {task_href}", err=True)
            if not background:
                result = self.wait_for_task(task_href)
                click.echo("Done.", err=True)
        return result

    def wait_for_task(self, task_href: str, timeout: int = 120) -> Any:
        while timeout:
            time.sleep(1)
            timeout -= 1
            task = self.api.call("tasks_read", parameters={"task_href": task_href})
            if task["state"] == "completed":
                return task
            elif task["state"] == "failed":
                raise click.ClickException(
                    f"Task {task_href} failed: '{task['error']['description']}'"
                )
            elif task["state"] == "canceled":
                raise click.ClickException("Task canceled")
            elif task["state"] in ["waiting", "running"]:
                click.echo(".", nl=False, err=True)
            else:
                raise NotImplementedError(f"Unknown task state: {task['state']}")
        raise click.ClickException("Task timed out")


class PulpEntityContext:
    # Subclasses should provide appropriate values here
    ENTITY: str = "entity"
    HREF: str = "entity_href"
    LIST_ID: str = "entities_list"
    READ_ID: str = "entities_read"
    CREATE_ID: str = "entities_create"
    UPDATE_ID: str = "entities_update"
    DELETE_ID: str = "entities_delete"

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


def _config_callback(ctx: click.Context, param: Any, value: str) -> None:
    if ctx.default_map:
        return

    if value:
        ctx.default_map = toml.load(value)["cli"]
    else:
        xdg_config_home = os.path.expanduser(os.environ.get("XDG_CACHE_HOME") or "~/.config")
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
    help="Increase verbosity. Explain api calls as they are made",
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
            debug_callback=lambda x: click.secho(x, err=True, bold=True) if verbose >= 1 else None,
        )
    except OpenAPIError as e:
        raise click.ClickException(str(e))
    ctx.obj = PulpContext(api=api, format=format)
