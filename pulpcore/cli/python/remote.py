import json
import typing as t

import click
from pulp_glue.common.context import PluginRequirement
from pulp_glue.common.i18n import get_translation
from pulp_glue.python.context import PulpPythonRemoteContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    common_remote_create_options,
    common_remote_update_options,
    create_command,
    destroy_command,
    href_option,
    label_command,
    list_command,
    load_json_callback,
    name_option,
    pass_pulp_context,
    pulp_group,
    pulp_option,
    remote_filter_options,
    resource_lookup_option,
    show_command,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


remote_lookup_option = resource_lookup_option(
    "--remote",
    context_class=PulpPythonRemoteContext,
)


def _package_list_callback(
    ctx: click.Context, param: click.Parameter, value: t.Optional[str]
) -> t.Any:
    """Parses the requirements file or JSON list for packages."""
    if not value:
        return value

    if value.startswith("@"):
        json_string = f'["{value[1:]}"]'
    else:
        json_string = value

    try:
        json_object = json.loads(json_string)
    except json.decoder.JSONDecodeError:
        raise click.ClickException(_("Failed to decode JSON: {}").format(json_string))
    else:
        package_list = list()
        for packages in json_object:
            package_list += parse_requirements_string(packages)
        return package_list


@pulp_group()
@click.option(
    "-t",
    "--type",
    "remote_type",
    type=click.Choice(["python"], case_sensitive=False),
    default="python",
)
@pass_pulp_context
@click.pass_context
def remote(ctx: click.Context, pulp_ctx: PulpCLIContext, remote_type: str) -> None:
    if remote_type == "python":
        ctx.obj = PulpPythonRemoteContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option, remote_lookup_option]
nested_lookup_options = [remote_lookup_option]
python_remote_options = [
    click.option(
        "--policy", type=click.Choice(["immediate", "on_demand", "streamed"], case_sensitive=False)
    ),
    click.option("--includes", callback=_package_list_callback, help=_("Package allowlist")),
    click.option("--excludes", callback=_package_list_callback, help=_("Package blocklist")),
    click.option("--prereleases", type=click.BOOL, default=True),
    pulp_option(
        "--keep-latest-packages",
        type=int,
        needs_plugins=[PluginRequirement("python", specifier=">=3.2.0")],
    ),
    pulp_option(
        "--package-types",
        callback=load_json_callback,
        needs_plugins=[PluginRequirement("python", specifier=">=3.2.0")],
    ),
    pulp_option(
        "--exclude-platforms",
        callback=load_json_callback,
        needs_plugins=[PluginRequirement("python", specifier=">=3.2.0")],
    ),
]

remote.add_command(list_command(decorators=remote_filter_options))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(create_command(decorators=common_remote_create_options + python_remote_options))
remote.add_command(
    update_command(decorators=lookup_options + common_remote_update_options + python_remote_options)
)
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(label_command(decorators=nested_lookup_options))


# TODO Add support for 'from_bandersnatch' remote create endpoint
def parse_requirements_string(requirements_string: str) -> t.List[str]:
    """Parses the requirements string to find the packages listed."""
    requirements_string = requirements_string.strip()
    if not requirements_string or requirements_string.startswith("#"):
        return []
    requirements_string, *_ = requirements_string.split("#", maxsplit=1)
    requirements_string = requirements_string.strip()
    if requirements_string.endswith(".txt"):
        *_, requirements_file = requirements_string.split()
        return parse_requirements_file(requirements_file)
    else:
        return [requirements_string]


def parse_requirements_file(requirements_file: str) -> t.List[str]:
    """Parses the requirements.txt file."""
    requirements = list()
    try:
        with click.open_file(requirements_file) as fp:
            for line in fp.readlines():
                requirements += parse_requirements_string(line)
    except OSError:
        raise click.ClickException(
            _("Failed to load content from {requirements_file}").format(
                requirements_file=requirements_file
            )
        )
    return requirements
