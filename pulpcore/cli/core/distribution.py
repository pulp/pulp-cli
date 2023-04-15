import click
from pulp_glue.common.context import PluginRequirement, PulpDistributionContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    distribution_filter_options,
    list_command,
    pass_pulp_context,
    pulp_group,
)


@pulp_group()
@pass_pulp_context
@click.pass_context
def distribution(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    """
    Perform actions on all distribution.

    Please look for the plugin specific distribution commands for more detailed actions.
    i.e. 'pulp file distribution <...>'
    """
    pulp_ctx.needs_plugin(PluginRequirement("core", specifier=">=3.19.0"))
    ctx.obj = PulpDistributionContext(pulp_ctx)


distribution.add_command(list_command(decorators=distribution_filter_options))
