from typing import Any, Optional

import pkg_resources
import click
import os

import toml

from pulpcore.cli.common.openapi import OpenAPI, OpenAPIError
from pulpcore.cli.common.context import (
    PulpContext,
)


__version__ = "0.1.0"


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
@click.option("--username", help="Username on pulp server")
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
@click.option("--refresh-api", is_flag=True, help="Invalidate cached API docs")
@click.option(
    "--dry-run", is_flag=True, help="Trace commands without performing any unsafe HTTP calls"
)
@click.pass_context
def main(
    ctx: click.Context,
    base_url: str,
    username: Optional[str],
    password: Optional[str],
    verify_ssl: bool,
    format: str,
    verbose: int,
    background: bool,
    refresh_api: bool,
    dry_run: bool,
) -> None:
    if username and not password:
        password = click.prompt("password", hide_input=True)
    try:
        api = OpenAPI(
            base_url=base_url,
            doc_path="/pulp/api/v3/docs/api.json",
            username=username,
            password=password,
            validate_certs=verify_ssl,
            refresh_cache=refresh_api,
            safe_calls_only=dry_run,
            debug_callback=lambda level, x: click.secho(x, err=True, bold=True)
            if verbose >= level
            else None,
        )
    except OpenAPIError as e:
        raise click.ClickException(str(e))
    ctx.obj = PulpContext(api=api, format=format, background_tasks=background)


##############################################################################
# Load plugins
# https://packaging.python.org/guides/creating-and-discovering-plugins/#using-package-metadata
discovered_plugins = {
    entry_point.name: entry_point.load()
    for entry_point in pkg_resources.iter_entry_points("pulp_cli.plugins")
}
