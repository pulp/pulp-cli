from typing import Any, Optional

import click
import datetime
import json
import os
import time

import toml

from pulpcore.cli.openapi import OpenAPI, OpenAPIError


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

        # define some names
        self.href_key: Optional[str] = None
        self.list_id: Optional[str] = None
        self.cancel_id: Optional[str] = None

    def output_result(self, result: Any) -> None:
        if self.format == "json":
            click.echo(json.dumps(result, cls=PulpJSONEncoder, indent=2))
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
            if task["state"] == "failed":
                raise click.ClickException(
                    f"Task {task_href} failed: '{task['error']['description']}'"
                )
            if task["state"] == "canceled":
                raise click.ClickException("Task canceled")
            click.echo(".", nl=False, err=True)
        raise click.ClickException("Task timed out")


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
@click.option("--format", type=click.Choice(["json", "none"], case_sensitive=False), default="json")
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
