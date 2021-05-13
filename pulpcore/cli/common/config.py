import gettext
from pathlib import Path
from typing import Any, Callable, Dict, List, MutableMapping

import click
import toml

_ = gettext.gettext

CONFIG_LOCATION = str(Path(click.utils.get_app_dir("pulp"), "settings.toml"))
FORMAT_CHOICES = ["json", "yaml", "none"]
SETTINGS = ["base_url", "username", "password", "cert", "key", "verify_ssl", "format", "dry_run"]

CONFIG_OPTIONS = [
    click.option("--base-url", default="https://localhost", help=_("API base url")),
    click.option("--username", default="", help=_("Username on pulp server")),
    click.option("--password", default="", help=_("Password on pulp server")),
    click.option("--cert", default="", help=_("Path to client certificate")),
    click.option(
        "--key",
        default="",
        help=_("Path to client private key. Not required if client cert contains this."),
    ),
    click.option("--verify-ssl/--no-verify-ssl", default=True, help=_("Verify SSL connection")),
    click.option(
        "--format",
        type=click.Choice(FORMAT_CHOICES, case_sensitive=False),
        default="json",
        help=_("Format of the response"),
    ),
    click.option(
        "--dry-run/--force",
        default=False,
        help=_("Trace commands without performing any unsafe HTTP calls"),
    ),
]


def config_options(command: Callable[..., Any]) -> Callable[..., Any]:
    for option in reversed(CONFIG_OPTIONS):
        command = option(command)
    return command


def validate_config(config: Dict[str, Any], strict: bool = False) -> bool:
    """Validate, that the config provides the proper data types"""
    errors: List[str] = []
    if "format" in config and config["format"].lower() not in FORMAT_CHOICES:
        errors.append(_("'format' is not one of {}").format(FORMAT_CHOICES))
    if "dry_run" in config and not isinstance(config["dry_run"], bool):
        errors.append(_("'dry_run' is not a bool"))
    unknown_settings = set(config.keys()) - set(SETTINGS)
    if unknown_settings:
        errors.append(_("Unknown settings: '{}'.").format("','".join(unknown_settings)))
    if strict:
        missing_settings = set(SETTINGS) - set(config.keys())
        if missing_settings:
            errors.append(_("Missing settings: '{}'.").format("','".join(missing_settings)))
    if errors:
        raise ValueError("\n".join(errors))
    return True


def validate_settings(settings: MutableMapping[str, Dict[str, Any]], strict: bool = False) -> bool:
    errors: List[str] = []
    if "cli" not in settings:
        errors.append(_("Could not locate default profile 'cli' setting"))

    for key, profile in settings.items():
        if key != "cli" and not key.startswith("cli-"):
            if strict:
                errors.append(_("Invalid profile '{}'").format(key))
            continue
        try:
            validate_config(profile, strict=strict)
        except ValueError as e:
            errors.append(_("Profile {}:").format(key))
            errors.append(str(e))
    if errors:
        raise ValueError("\n".join(errors))
    return True


@click.group(name="config", help=_("Manage pulp-cli config file"))
def config() -> None:
    pass


@config.command(help=_("Create a pulp-cli config settings file"))
@config_options
@click.option("--interactive", "-i", is_flag=True)
@click.option("--editor", "-e", is_flag=True, help=_("Edit the config file in an editor"))
@click.option("--overwrite", "-o", is_flag=True, help=_("Overwite any existing config file"))
@click.option("--location", default=CONFIG_LOCATION, type=click.Path(resolve_path=True))
@click.pass_context
def create(
    ctx: click.Context,
    interactive: bool,
    editor: bool,
    overwrite: bool,
    location: str,
    **kwargs: Any,
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
        return click.prompt(help, default=(option.default), type=option.type)

    settings: MutableMapping[str, Any] = kwargs

    if interactive:
        location = click.prompt("Config file location", default=location)
        _check_location(location)
        for setting in SETTINGS:
            settings[setting] = prompt_config_option(setting)
    else:
        _check_location(location)

    output = toml.dumps({"cli": settings})

    if editor:
        output = click.edit(output)
        if not output:
            raise click.ClickException("No output from editor. Aborting.")
    try:
        settings = toml.loads(output)
        validate_settings(settings)
    except (ValueError, toml.TomlDecodeError) as e:
        raise click.ClickException(str(e))

    Path(location).parent.mkdir(parents=True, exist_ok=True)
    with Path(location).open("w") as sfile:
        sfile.write(output)

    click.echo(f"Created config file at '{location}'.")


@config.command(help=_("Open the settings config file in an editor"))
@click.option("--location", default=CONFIG_LOCATION, type=click.Path(resolve_path=True))
def edit(location: str) -> None:
    if not Path(location).exists():
        raise click.ClickException(
            f"File '{location}' does not exists. If you wish to create the file, use the pulp "
            "create command."
        )

    with Path(location).open("r") as sfile:
        output = sfile.read()
    while True:
        output = click.edit(output)
        if not output:
            raise click.ClickException("No output from editor. Aborting.")
        try:
            settings = toml.loads(output)
            validate_settings(settings)
            break
        except (ValueError, toml.TomlDecodeError) as e:
            click.echo(str(e), err=True)
            click.confirm(_("Retry"), abort=True)
    with Path(location).open("w") as sfile:
        sfile.write(output)


@config.command(help=_("Validate a pulp-cli config file"))
@click.option("--location", default=CONFIG_LOCATION, type=click.Path(resolve_path=True))
@click.option("--strict", is_flag=True, help=_("Validate that all settings are present"))
def validate(location: str, strict: bool) -> None:
    try:
        settings = toml.load(location)
    except toml.TomlDecodeError:
        raise click.ClickException(_("Invalid toml file '{location}'.").format(location=location))

    try:
        validate_settings(settings, strict)
    except ValueError as e:
        raise click.ClickException(str(e))

    click.echo(f"File '{location}' is a valid pulp-cli config.")
