import click
import datetime
import json
import os
import time

import toml

from pulpcore.cli.openapi import OpenAPI


class PulpJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            super(json.JSONEncoder).default(obj)


class PulpContext:
    def output_result(self, result):
        if self.format == "json":
            click.echo(json.dumps(result, cls=PulpJSONEncoder, indent=2))

    def call(self, operation_id, background=False, *args, **kwargs):
        result = self.api.call(operation_id, *args, **kwargs)
        if "task" in result:
            task_href = result["task"]
            click.echo(f"Started task {task_href}", err=True)
            if not background:
                result = self.wait_for_task(task_href)
                click.echo("Done.", err=True)
        return result

    def wait_for_task(self, task_href, timeout=120):
        while timeout:
            timeout -= 1
            task = self.api.call("tasks_read", parameters={"task_href": task_href})
            if task["state"] == "completed":
                return task
            if task["state"] == "failed":
                raise click.ClickException("Task failed")
            if task["state"] == "canceled":
                raise click.ClickException("Task canceled")
            time.sleep(1)
            timeout -= 1
            click.echo(".", nl=False, err=True)
        raise click.ClickException("Task timed out")


def _config_callback(ctx, param, value):
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
# @click.option("--password", prompt=True, hide_input=True, help="Password on pulp server")
@click.option("--password", help="Password on pulp server")
@click.option("--verify-ssl/--no-verify-ssl", default=True, help="Verify SSL connection")
@click.option("--format", type=click.Choice(["json"], case_sensitive=False), default="json")
@click.pass_context
def main(ctx, base_url, user, password, verify_ssl, format):
    ctx.ensure_object(PulpContext)
    ctx.obj.api = OpenAPI(
        base_url=base_url,
        doc_path="/pulp/api/v3/docs/api.json",
        username=user,
        password=password,
        validate_certs=verify_ssl,
        refresh_cache=True,
    )
    ctx.obj.format = format
