import os
import sys
import typing as t
from types import ModuleType

import click
import toml
from pulp_glue.common.i18n import get_translation

from pulp_cli.config import CONFIG_LOCATIONS, config, config_options, validate_config
from pulpcore.cli.common.generic import PulpCLIContext, pulp_group

if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points

try:
    from click_shell import make_click_shell

    HAS_CLICK_SHELL = True
except ImportError:
    HAS_CLICK_SHELL = False

__version__ = "0.29.1"
translation = get_translation(__package__)
_ = translation.gettext
# Keep track to prevent loading plugins twice
loaded_plugins: t.MutableMapping[str, ModuleType] = {}


def load_plugins(
    enabled_plugins: t.Optional[t.List[str]] = None,
) -> t.MutableMapping[str, ModuleType]:
    ##############################################################################
    # Load plugins
    # https://packaging.python.org/guides/creating-and-discovering-plugins/#using-package-metadata

    discovered_plugins: t.Dict[str, ModuleType] = {
        entry_point.name: entry_point.load()
        for entry_point in entry_points(group="pulp_cli.plugins")
        if (enabled_plugins is None or entry_point.name in enabled_plugins)
        and entry_point.name not in loaded_plugins
    }
    for name, plugin in discovered_plugins.items():
        plugin.mount(main, discovered_plugins=discovered_plugins)
        loaded_plugins[name] = plugin
    return loaded_plugins


##############################################################################
# Main entry point


PLUGIN_KEY = f"{__name__}.plugins"
CONFIG_KEY = f"{__name__}.config"
PROFILE_KEY = f"{__name__}.profile"


# config and config-profile need to be combined in order to fetch the desired defaults.
# Click will call both these callbacks exactly once, but we cannot know the order.
# Therefore whichever one has seen the that the other deposited it's value will coninue with
# _load_config (also to be called exactly once).


def _config_callback(ctx: click.Context, param: t.Any, value: t.Optional[str]) -> None:
    ctx.meta[CONFIG_KEY] = value
    if PROFILE_KEY in ctx.meta:
        _load_config(ctx)


def _config_profile_callback(ctx: click.Context, param: t.Any, value: t.Optional[str]) -> None:
    ctx.meta[PROFILE_KEY] = value
    if CONFIG_KEY in ctx.meta:
        _load_config(ctx)


def _load_config(ctx: click.Context) -> None:
    # Raise a runtime error if called a second time.
    assert ctx.default_map is None

    enabled_plugins: t.Optional[t.List[str]] = None
    try:
        config_path = ctx.meta[CONFIG_KEY]
        profile_key = ctx.meta[PROFILE_KEY]
        if config_path is not None:
            config = toml.load(config_path)
        else:
            config = {"cli": {}}
            for location in CONFIG_LOCATIONS:
                try:
                    new_config = toml.load(location)
                except (FileNotFoundError, PermissionError):
                    pass
                else:
                    if location.endswith("settings.toml"):
                        click.echo(
                            _(
                                "Warning: "
                                "Using '{location}' for the pulp-cli configuration is deprecated.\n"
                                "Please move your config to '{new_location}'."
                            ).format(location=location, new_location=CONFIG_LOCATIONS[-1]),
                            err=True,
                        )

                    # level 1 merge
                    for key in new_config:
                        if key in config:
                            config[key].update(new_config[key])
                        else:
                            config[key] = new_config[key]
        profile: str = "cli"
        if profile_key is not None:
            profile = "cli-" + profile_key
        try:
            validate_config(config[profile])
            enabled_plugins = config[profile].pop("plugins", None)
            ctx.default_map = config[profile]
        except KeyError:
            raise click.ClickException(
                _("Config profile named '{profile}' not found.").format(profile=profile)
            )
    except ValueError as e:
        click.echo(_("Config file failed to parse. ({}).").format(e), err=True)
        if not sys.stdout.isatty() or not click.confirm(_("Continue without config?")):
            raise click.ClickException(_("Aborted."))
    ctx.meta[PLUGIN_KEY] = load_plugins(enabled_plugins)


def _version_callback(ctx: click.Context, param: t.Any, value: bool) -> None:
    if value:
        click.echo(_("Pulp3 Command Line Interface, Version {}").format(__version__))
        click.echo(_("Plugin Versions:"))
        for name, plugin in ctx.meta[PLUGIN_KEY].items():
            version = getattr(plugin, "__version__", None)
            if version:
                click.echo(f"  {name}: {version}")
        # If we ever decouple the glue parts, we should list the versions here too.
        ctx.exit(0)


@click.option(
    "--profile",
    "-p",
    envvar="PULP_CLI_PROFILE",
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
    is_eager=True,
)
@click.option(
    "--version",
    help=_("Show CLI version information and exit."),
    is_flag=True,
    callback=_version_callback,
    expose_value=False,
)
@click.option(
    "-b",
    "--background",
    is_flag=True,
    help=_("Start tasks in the background instead of awaiting them"),
)
@click.option("--refresh-api", is_flag=True, help=_("Invalidate cached API docs"))
@click.option(
    "--cid",
    help=_(
        "Logging CID to send on requests"
        " (note: server configuration may require a valid GUID and ignore CIDs that aren't)"
    ),
)
@config_options
@pulp_group(no_args_is_help=False)
@click.pass_context
def main(
    ctx: click.Context,
    base_url: str,
    api_root: str,
    domain: str,
    headers: t.List[str],
    username: t.Optional[str],
    password: t.Optional[str],
    client_id: t.Optional[str],
    client_secret: t.Optional[str],
    cert: t.Optional[str],
    key: t.Optional[str],
    verify_ssl: bool,
    format: str,
    verbose: int,
    background: bool,
    refresh_api: bool,
    dry_run: bool,
    timeout: int,
    cid: str,
) -> None:
    def _debug_callback(level: int, x: str) -> None:
        if verbose >= level:
            click.secho(x, err=True, bold=True)

    api_kwargs = dict(
        base_url=base_url,
        headers=dict((header.split(":", maxsplit=1) for header in headers)),
        cert=cert,
        key=key,
        validate_certs=verify_ssl,
        refresh_cache=refresh_api,
        safe_calls_only=dry_run,
        debug_callback=_debug_callback,
        user_agent=f"Pulp-CLI/{__version__}",
        cid=cid,
    )
    ctx.obj = PulpCLIContext(
        api_root=api_root,
        api_kwargs=api_kwargs,
        domain=domain,
        format=format,
        background_tasks=background,
        timeout=timeout,
        username=username,
        password=password,
        oauth2_client_id=client_id,
        oauth2_client_secret=client_secret,
    )


main.add_command(config)


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
