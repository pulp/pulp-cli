import click
from pulp_glue.common.context import PluginRequirement
from pulp_glue.common.i18n import get_translation
from pulp_glue.python.context import (
    PulpPythonDistributionContext,
    PulpPythonRemoteContext,
    PulpPythonRepositoryContext,
)

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    common_distribution_create_options,
    content_guard_option,
    create_command,
    destroy_command,
    distribution_filter_options,
    distribution_lookup_option,
    href_option,
    label_command,
    list_command,
    name_option,
    pass_pulp_context,
    pulp_group,
    pulp_labels_option,
    pulp_option,
    resource_option,
    show_command,
    update_command,
)

translation = get_translation(__package__)
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
    href_pattern=PulpPythonRepositoryContext.HREF_PATTERN,
)


@pulp_group()
@click.option(
    "-t",
    "--type",
    "distribution_type",
    type=click.Choice(["python"], case_sensitive=False),
    default="python",
)
@pass_pulp_context
@click.pass_context
def distribution(ctx: click.Context, pulp_ctx: PulpCLIContext, distribution_type: str) -> None:
    if distribution_type == "python":
        ctx.obj = PulpPythonDistributionContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option, distribution_lookup_option]
nested_lookup_options = [distribution_lookup_option]
update_options = [
    click.option(
        "--publication",
        help=_(
            "Publication to be served. This will unset the 'repository' and disable "
            "auto-distribute."
        ),
    ),
    repository_option,
    content_guard_option,
    pulp_option(
        "--allow-uploads/--block-uploads",
        needs_plugins=[PluginRequirement("python", specifier=">=3.4.0")],
        default=None,
    ),
    resource_option(
        "--remote",
        default_plugin="python",
        default_type="python",
        context_table={"python:python": PulpPythonRemoteContext},
        needs_plugins=[PluginRequirement("python", specifier=">=3.6.0")],
        href_pattern=PulpPythonRemoteContext.HREF_PATTERN,
    ),
    pulp_labels_option,
]
create_options = common_distribution_create_options + update_options

distribution.add_command(list_command(decorators=distribution_filter_options))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(create_command(decorators=create_options))
distribution.add_command(
    update_command(decorators=lookup_options + update_options + [click.option("--base-path")])
)
distribution.add_command(destroy_command(decorators=lookup_options))
distribution.add_command(label_command(decorators=nested_lookup_options))
