import click
from pulp_glue.common.context import PulpRemoteContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    list_command,
    pass_pulp_context,
    pulp_group,
    remote_filter_options,
)


@pulp_group()
@pass_pulp_context
@click.pass_context
def remote(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    """
    Perform actions on all remotes.

    Please look for the plugin specific remote commands for more detailed actions.
    i.e. 'pulp file remote <...>'
    """
    ctx.obj = PulpRemoteContext(pulp_ctx)


remote.add_command(list_command(decorators=remote_filter_options))
