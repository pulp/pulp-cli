import re
import typing as t
from pathlib import Path
from urllib.parse import urlparse

import click
import toml
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import REGISTERED_OUTPUT_FORMATTERS, pulp_group

translation = get_translation(__package__)
_ = translation.gettext

_T = t.TypeVar("_T")
_AnyCallable = t.Callable[..., t.Any]
FC = t.TypeVar("FC", bound=t.Union[_AnyCallable, click.Command])

CONFIG_LOCATIONS = [
    "/etc/pulp/cli.toml",
    str(Path(click.utils.get_app_dir("pulp"), "settings.toml")),
    str(Path(click.utils.get_app_dir("pulp"), "cli.toml")),
]
FORMAT_CHOICES = list(REGISTERED_OUTPUT_FORMATTERS.keys())
SETTINGS = [
    "base_url",
    "api_root",
    "domain",
    "headers",
    "username",
    "password",
    "client_id",
    "client_secret",
    "cert",
    "key",
    "verify_ssl",
    "format",
    "dry_run",
    "timeout",
    "verbose",
    "plugins",
]

CONFIG_OPTIONS = [
    click.option("--base-url", default="https://localhost", help=_("API base url")),
    click.option(
        "--api-root",
        default="/pulp/",
        help=_("Absolute API base path on server (not including 'api/v3/')"),
    ),
    click.option("--domain", default="default", help=_("Domain to work in if feature is enabled")),
    click.option(
        "--header",
        "headers",
        multiple=True,
        help=_(
            "Custom header to add to each api call. "
            "Name and value are colon separated. "
            "Can be specified multiple times."
        ),
    ),
    click.option("--username", default=None, help=_("Username on pulp server")),
    click.option("--password", default=None, help=_("Password on pulp server")),
    click.option("--client-id", default=None, help=_("OAuth2 client ID")),
    click.option("--client-secret", default=None, help=_("OAuth2 client secret")),
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
    click.option(
        "--timeout",
        "-T",
        type=int,
        default=0,
        help=_("Time to wait for background tasks, set to 0 to wait infinitely"),
    ),
    click.option(
        "-v",
        "--verbose",
        type=int,
        count=True,
        help=_("Increase verbosity; explain api calls as they are made"),
    ),
]


def not_none(value: t.Optional[_T], exc: t.Optional[Exception] = None) -> _T:
    if value is None:
        raise exc or RuntimeError(_("Value cannot be None."))
    return value


def config_options(command: FC) -> FC:
    for option in reversed(CONFIG_OPTIONS):
        command = option(command)
    return command


def validate_config(config: t.Dict[str, t.Any], strict: bool = False) -> None:
    """Validate, that the config provides the proper data types"""
    errors: t.List[str] = []
    if "base_url" in config:
        try:
            parsed_url = urlparse(config["base_url"])
            if (
                not parsed_url.scheme
                or not parsed_url.netloc
                or parsed_url.path
                or parsed_url.params
                or parsed_url.query
                or parsed_url.fragment
            ):
                errors.append(_("'base_url' should be of the form '<schema>://<netloc>'"))
        except ValueError:
            errors.append(_("Failed to parse the 'base_path'."))
    if "api_root" in config and (config["api_root"][0] != "/" or config["api_root"][-1] != "/"):
        errors.append(_("'api_root' must begin and end with '/'"))
    if "format" in config and config["format"].lower() not in FORMAT_CHOICES:
        errors.append(_("'format' is not one of {choices}").format(choices=FORMAT_CHOICES))
    if "dry_run" in config and not isinstance(config["dry_run"], bool):
        errors.append(_("'dry_run' is not a bool"))
    if "timeout" in config and not isinstance(config["timeout"], int):
        errors.append(_("'timeout' is not an integer"))
    if "verbose" in config and not isinstance(config["verbose"], int):
        errors.append(_("'verbose' is not an integer"))
    if "domain" in config and not re.match(r"^[-a-zA-Z0-9_]+\Z", config["domain"]):
        errors.append(_("'domain' must be a slug string"))
    if "headers" in config:
        if not isinstance(config["headers"], list) or not all(
            (
                isinstance(header, str)
                and re.match(r"^[-a-zA-Z0-9_]+\s*:\s*[-a-zA-Z0-9_]+$", header)
                for header in config["headers"]
            )
        ):
            errors.append(_("'headers' must be a list of strings with a colon separator"))
    if "plugins" in config and not (
        isinstance(config["plugins"], list)
        and all((isinstance(item, str) for item in config["plugins"]))
    ):
        errors.append(_("'plugins' must be a list of strings"))
    unknown_settings = set(config.keys()) - set(SETTINGS)
    if unknown_settings:
        errors.append(_("Unknown settings: '{}'.").format("','".join(unknown_settings)))
    if strict:
        missing_settings = (
            set(SETTINGS)
            - set(config.keys())
            - {"plugins", "username", "password", "client_id", "client_secret"}
        )
        if missing_settings:
            errors.append(_("Missing settings: '{}'.").format("','".join(missing_settings)))
    if errors:
        raise ValueError("\n".join(errors))


def validate_settings(
    settings: t.MutableMapping[str, t.Dict[str, t.Any]], strict: bool = False
) -> None:
    errors: t.List[str] = []
    if "cli" not in settings:
        errors.append(_("Could not locate default profile 'cli' setting"))

    for key, profile in settings.items():
        if key != "cli" and not key.startswith("cli-"):
            if strict:
                errors.append(_("Invalid profile '{key}'").format(key=key))
            continue
        try:
            validate_config(profile, strict=strict)
        except ValueError as e:
            errors.append(_("Profile {key}:").format(key=key))
            errors.append(str(e))
    if errors:
        raise ValueError("\n".join(errors))


@pulp_group(name="config", help=_("Manage pulp-cli config file"))
def config() -> None:
    pass


# This is a mypy bug getting confused with positional args
# https://github.com/python/mypy/issues/15037
@config.command(help=_("Create a pulp-cli config settings file"))  # type: ignore [arg-type]
@config_options
@click.option(
    "--plugin",
    "plugins",
    multiple=True,
    help=_("Select pluins supposed to be loaded. Can be specified multiple times"),
)
@click.option("--interactive", "-i", is_flag=True)
@click.option("--editor", "-e", is_flag=True, help=_("Edit the config file in an editor"))
@click.option("--overwrite", "-o", is_flag=True, help=_("Overwrite any existing config file"))
@click.option("--location", default=CONFIG_LOCATIONS[-1], type=click.Path(resolve_path=True))
@click.pass_context
def create(
    ctx: click.Context,
    interactive: bool,
    editor: bool,
    overwrite: bool,
    location: str,
    **kwargs: t.Any,
) -> None:
    def _check_location(location: str) -> None:
        if not overwrite and Path(location).exists():
            raise click.ClickException(
                _(
                    "File '{location}' already exists. Use --overwrite if you want to overwrite it."
                ).format(location=location)
            )

    def prompt_config_option(name: str) -> t.Any:
        """Find the option from the root command and prompt."""
        option = next(p for p in ctx.command.params if p.name == name)
        if option.multiple:
            assert option.type == click.types.STRING
            assert option.default is None
            result = []
            value = click.prompt(f"{name} (end with an empty line)", default="", type=option.type)
            while value:
                result.append(value)
                value = click.prompt(f"{name} (continued)", default="", type=option.type)
            return result
        else:
            return click.prompt(name, default=option.default, type=option.type)

    settings: t.MutableMapping[str, t.Any] = kwargs
    if not settings["plugins"]:
        settings["plugins"] = None

    if interactive:
        location = click.prompt(_("Config file location"), default=location)
        _check_location(location)
        for setting in SETTINGS:
            settings[setting] = prompt_config_option(setting)
    else:
        _check_location(location)

    output: str = toml.dumps({"cli": settings})

    if editor:
        output = not_none(
            click.edit(output), click.ClickException(_("No output from editor. Aborting."))
        )
    try:
        settings = toml.loads(output)
        validate_settings(settings)
    except (ValueError, toml.TomlDecodeError) as e:
        raise click.ClickException(str(e))

    Path(location).parent.mkdir(parents=True, exist_ok=True)
    with Path(location).open("w") as sfile:
        sfile.write(output)

    click.echo(_("Created config file at '{location}'.").format(location=location))


@config.command(help=_("Open the settings config file in an editor"))
@click.option("--location", default=CONFIG_LOCATIONS[-1], type=click.Path(resolve_path=True))
def edit(location: str) -> None:
    if not Path(location).exists():
        raise click.ClickException(
            _(
                "File '{location}' does not exists. If you wish to create the file, use the pulp "
                "create command."
            ).format(location=location)
        )

    with Path(location).open("r") as sfile:
        output: str = sfile.read()
    while True:
        output = not_none(
            click.edit(output), click.ClickException(_("No output from editor. Aborting."))
        )
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
@click.option("--location", default=CONFIG_LOCATIONS[-1], type=click.Path(resolve_path=True))
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

    click.echo(_("File '{location}' is a valid pulp-cli config.").format(location=location))
