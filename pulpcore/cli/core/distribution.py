import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import distribution_filter_options, list_command, pulp_group
from pulpcore.cli.core.context import PulpDistributionContext


@pulp_group()
@pass_pulp_context
@click.pass_context
def distribution(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    """
    Perform actions on all distribution.

    Please look for the plugin specific distribution commands for more detailed actions.
    i.e. 'pulp file distribution <...>'
    """
    pulp_ctx.needs_plugin(PluginRequirement("core", "3.19.0"))
    ctx.obj = PulpDistributionContext(pulp_ctx)


distribution.add_command(list_command(decorators=distribution_filter_options))
