import gettext
import os
import sys
from typing import Any, Optional

import click
import pkg_resources
import toml

try:
    from click_shell import make_click_shell

    HAS_CLICK_SHELL = True
except ImportError:
    HAS_CLICK_SHELL = False

from pulpcore.cli.common.config import CONFIG_LOCATIONS, config, config_options, validate_config
from pulpcore.cli.common.context import PulpContext
from pulpcore.cli.common.debug import debug

_ = gettext.gettext
__version__ = "0.11.0"


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

    try:
        if value:
            config = toml.load(value)
        else:
            config = {"cli": {}}
            for location in CONFIG_LOCATIONS:
                try:
                    new_config = toml.load(location)
                    # level 1 merge
                    for key in new_config:
                        if key in config:
                            config[key].update(new_config[key])
                        else:
                            config[key] = new_config[key]
                except FileNotFoundError:
                    pass
        profile: str = "cli"
        if PROFILE_KEY in ctx.meta:
            profile = "cli-" + ctx.meta[PROFILE_KEY]
        try:
            validate_config(config[profile])
            ctx.default_map = config[profile]
        except KeyError:
            raise click.ClickException(
                _("Profile named '{profile}' not found.").format(profile=profile)
            )
    except ValueError as e:
        if sys.stdout.isatty():
            click.echo(_("Config file failed to parse. ({}).").format(e), err=True)
            if click.confirm(_("Continue without config?")):
                return
        raise click.ClickException(_("Aborted."))


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
    help=_("Path of a Pulp CLI settings file to use instead of the default location"),
    callback=_config_callback,
    expose_value=False,
)
@click.option(
    "-b",
    "--background",
    is_flag=True,
    help=_("Start tasks in the background instead of awaiting them"),
)
@click.option("--refresh-api", is_flag=True, help=_("Invalidate cached API docs"))
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
    timeout: int,
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
    ctx.obj = PulpContext(
        api_kwargs=api_kwargs, format=format, background_tasks=background, timeout=timeout
    )


main.add_command(config)
main.add_command(debug)


if HAS_CLICK_SHELL:

    @main.command("shell")
    @click.pass_context
    def pulp_shell(ctx: click.Context) -> None:
        """Activate an interactive shell-mode"""
        make_click_shell(
            ctx.parent,
            prompt="pulp> ",
            intro="Starting Pulp3 interactive shell...",
            hist_file=os.path.join(click.utils.get_app_dir("pulp"), "cli-history"),
        ).cmdloop()


##############################################################################
# Load plugins
# https://packaging.python.org/guides/creating-and-discovering-plugins/#using-package-metadata
discovered_plugins = {
    entry_point.name: entry_point.load()
    for entry_point in pkg_resources.iter_entry_points("pulp_cli.plugins")
}
