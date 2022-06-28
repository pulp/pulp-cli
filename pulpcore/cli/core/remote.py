import click

from pulpcore.cli.common.context import PulpContext, PulpRemoteContext, pass_pulp_context
from pulpcore.cli.common.generic import list_command, pulp_group, remote_filter_options


@pulp_group()
@pass_pulp_context
@click.pass_context
def remote(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    """
    Perform actions on all remotes.

    Please look for the plugin specific remote commands for more detailed actions.
    i.e. 'pulp file remote <...>'
    """
    ctx.obj = PulpRemoteContext(pulp_ctx)


remote.add_command(list_command(decorators=remote_filter_options))
