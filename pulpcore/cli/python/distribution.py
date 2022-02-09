import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    base_path_contains_option,
    base_path_option,
    create_command,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    pulp_option,
    resource_option,
    show_command,
    update_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.python.context import (
    PulpPythonDistributionContext,
    PulpPythonRemoteContext,
    PulpPythonRepositoryContext,
)

translation = get_translation(__name__)
_ = translation.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="python",
    default_type="python",
    context_table={"python:python": PulpPythonRepositoryContext},
    help=_(
        "Repository to be used for auto-distributing."
        " When set, this will unset the 'publication'."
        " Specified as '[[<plugin>:]<type>:]<name>' or as href."
    ),
)

remote_option = resource_option(
    "--remote",
    default_plugin="python",
    default_type="python",
    context_table={"python:python": PulpPythonRemoteContext},
    needs_plugins=[PluginRequirement("python", "3.6.0.dev")],
)


@click.group()
@click.option(
    "-t",
    "--type",
    "distribution_type",
    type=click.Choice(["python"], case_sensitive=False),
    default="python",
)
@pass_pulp_context
@click.pass_context
def distribution(ctx: click.Context, pulp_ctx: PulpContext, distribution_type: str) -> None:
    if distribution_type == "python":
        ctx.obj = PulpPythonDistributionContext(pulp_ctx)
    else:
        raise NotImplementedError()


filter_options = [label_select_option, base_path_option, base_path_contains_option]
lookup_options = [href_option, name_option]
update_options = [
    click.option("--base-path"),
    click.option(
        "--publication",
        help=_(
            "Publication to be served. This will unset the 'repository' and disable "
            "auto-distribute."
        ),
    ),
    repository_option,
    pulp_option(
        "--allow-uploads/--block-uploads",
        needs_plugins=[PluginRequirement("python", "3.4.0.dev")],
        default=None,
    ),
    remote_option,
]
create_options = update_options + [click.option("--name", required=True)]

distribution.add_command(list_command(decorators=filter_options))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(create_command(decorators=create_options))
distribution.add_command(update_command(decorators=lookup_options + update_options))
distribution.add_command(destroy_command(decorators=lookup_options))
distribution.add_command(label_command())
