import gettext
from pathlib import Path
from typing import Any, Optional

import click
import toml

from pulpcore.cli.common import config_options

_ = gettext.gettext

LOCATION = str(Path(click.utils.get_app_dir("pulp"), "settings.toml"))
SETTINGS = ["base_url", "username", "password", "cert", "key", "verify_ssl", "format"]


@click.group(name="config", help=_("Manage pulp-cli config file"))
def config() -> None:
    pass


@config.command(help=_("Create a pulp-cli config settings file"))
@config_options
@click.option("--interactive", "-i", is_flag=True)
@click.option("--editor", "-e", is_flag=True, help=_("Edit the config file in an editor"))
@click.option("--overwrite", "-o", is_flag=True, help=_("Overwite any existing config file"))
@click.option("--location", default=LOCATION, type=click.Path(resolve_path=True))
@click.option(
    "--format", type=click.Choice(["json", "yaml", "none"], case_sensitive=False), default="json"
)
@click.pass_context
def create(
    ctx: click.Context,
    interactive: bool,
    editor: bool,
    overwrite: bool,
    location: str,
    base_url: str,
    username: Optional[str],
    password: Optional[str],
    cert: Optional[str],
    key: Optional[str],
    verify_ssl: bool,
    format: str,
) -> None:
    def _check_location(loc: str) -> None:
        if not overwrite and Path(loc).exists():
            raise click.ClickException(
                f"File '{loc}' already exists. Use --overwite if you want to overwrite it."
            )

    def prompt_config_option(name: str) -> Any:
        """Find the option from the root command and prompt."""
        option = next(p for p in ctx.command.params if p.name == name)
        if isinstance(option, click.Option) and option.help:
            help = option.help
        else:
            help = option.name
        return click.prompt(help, default=(option.default or ""), type=option.type)

    settings = {}
    if interactive:
        location = click.prompt("Config file location", default=LOCATION)
        _check_location(location)
        for setting in SETTINGS:
            settings[setting] = prompt_config_option(setting)
    else:
        _check_location(location)
        for setting in SETTINGS:
            settings[setting] = locals()[setting] or ""

    output = f"[cli]\n{toml.dumps(settings)}"
    output = toml.dumps({"cli": settings})

    if editor:
        output = click.edit(output)
        if not output:
            raise click.ClickException("No output from editor. Aborting.")

    Path(location).parent.mkdir(parents=True, exist_ok=True)
    with Path(location).open("w") as sfile:
        sfile.write(output)

    click.echo(f"Created config file at '{location}'.")


@config.command(help=_("Open the settings config file in an editor"))
@click.option("--location", default=LOCATION, type=click.Path(resolve_path=True))
def edit(location: str) -> None:
    if not Path(location).exists():
        raise click.ClickException(
            f"File '{location}' does not exists. If you wish to create the file, use the pulp "
            "create command."
        )

    with Path(location).open("r+") as sfile:
        settings = sfile.read()
        output = click.edit(settings)
        if not output:
            raise click.ClickException("No output from editor. Aborting.")
        sfile.seek(0)
        sfile.write(output)


@config.command(help=_("Validate a pulp-cli config file"))
@click.option("--location", default=LOCATION, type=click.Path(resolve_path=True))
@click.option("--strict", is_flag=True, help=_("Validate that all settings are present"))
def validate(location: str, strict: bool) -> None:
    try:
        settings = toml.load(location)
    except toml.TomlDecodeError:
        raise click.ClickException(f"Invalid toml file '{location}'.")

    if "cli" not in settings:
        raise click.ClickException(f"Could not locate cli section in '{location}'.")

    for setting in settings["cli"]:
        if setting not in SETTINGS:
            raise click.ClickException(f"Detected unknown setting: '{setting}'.")

    if strict:
        for setting in SETTINGS:
            if setting not in settings["cli"]:
                raise click.ClickException(f"Missing setting: '{setting}'.")

    click.echo(f"File '{location}' is a valid pulp-cli config.")
