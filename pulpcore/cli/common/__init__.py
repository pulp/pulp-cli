import gettext
import os
from typing import Any, Callable, Optional

import click
import pkg_resources
import toml

from pulpcore.cli.common.context import PulpContext
from pulpcore.cli.common.debug import debug

_ = gettext.gettext
__version__ = "0.7.0"


##############################################################################
# Main entry point


PROFILE_KEY = f"{__name__}.profile"


def _config_profile_callback(ctx: click.Context, param: Any, value: Optional[str]) -> Optional[str]:
    if value is not None:
        ctx.meta[PROFILE_KEY] = value
    return value


def _config_callback(ctx: click.Context, param: Any, value: Optional[str]) -> None:
    if ctx.default_map:
        return

    if value:
        config = toml.load(value)
    else:
        default_config_path = os.path.join(click.utils.get_app_dir("pulp"), "settings.toml")

        try:
            config = toml.load(default_config_path)
        except FileNotFoundError:
            # No config, but also none requested
            return

    profile: str = "cli"
    if PROFILE_KEY in ctx.meta:
        profile = "cli-" + ctx.meta[PROFILE_KEY]
    try:
        ctx.default_map = config[profile]
    except KeyError:
        raise click.ClickException(
            _("Profile named '{profile}' not found.").format(profile=profile)
        )


CONFIG_OPTIONS = [
    click.option("--base-url", default="https://localhost", help=_("API base url")),
    click.option("--username", help=_("Username on pulp server")),
    click.option("--password", help=_("Password on pulp server")),
    click.option("--cert", help=_("Path to client certificate")),
    click.option(
        "--key",
        help=_("Path to client private key. Not required if client cert contains this."),
    ),
    click.option("--verify-ssl/--no-verify-ssl", default=True, help=_("Verify SSL connection")),
    click.option(
        "--format",
        type=click.Choice(["json", "yaml", "none"], case_sensitive=False),
        default="json",
        help=_("Format of the response"),
    ),
]


def config_options(command: Callable[..., Any]) -> Callable[..., Any]:
    for option in reversed(CONFIG_OPTIONS):
        command = option(command)
    return command


@click.group()
@click.version_option(prog_name=_("pulp3 command line interface"))
@click.option(
    "--profile",
    "-p",
    help=_("Config profile to use"),
    callback=_config_profile_callback,
    expose_value=False,
    is_eager=True,
)
@click.option(
    "--config",
    type=click.Path(resolve_path=True),
    help=_("Path to the Pulp settings.toml file"),
    callback=_config_callback,
    expose_value=False,
)
@click.option(
    "-v",
    "--verbose",
    type=int,
    count=True,
    help=_("Increase verbosity; explain api calls as they are made"),
)
@click.option(
    "-b",
    "--background",
    is_flag=True,
    help=_("Start tasks in the background instead of awaiting them"),
)
@click.option("--refresh-api", is_flag=True, help=_("Invalidate cached API docs"))
@click.option(
    "--dry-run", is_flag=True, help=_("Trace commands without performing any unsafe HTTP calls")
)
@config_options
@click.pass_context
def main(
    ctx: click.Context,
    base_url: str,
    username: Optional[str],
    password: Optional[str],
    cert: Optional[str],
    key: Optional[str],
    verify_ssl: bool,
    format: str,
    verbose: int,
    background: bool,
    refresh_api: bool,
    dry_run: bool,
) -> None:
    def _debug_callback(level: int, x: str) -> None:
        if verbose >= level:
            click.secho(x, err=True, bold=True)

    api_kwargs = dict(
        base_url=base_url,
        doc_path="/pulp/api/v3/docs/api.json",
        username=username,
        password=password,
        cert=cert,
        key=key,
        validate_certs=verify_ssl,
        refresh_cache=refresh_api,
        safe_calls_only=dry_run,
        debug_callback=_debug_callback,
    )
    ctx.obj = PulpContext(api_kwargs=api_kwargs, format=format, background_tasks=background)


main.add_command(debug)


##############################################################################
# Load plugins
# https://packaging.python.org/guides/creating-and-discovering-plugins/#using-package-metadata
discovered_plugins = {
    entry_point.name: entry_point.load()
    for entry_point in pkg_resources.iter_entry_points("pulp_cli.plugins")
}
