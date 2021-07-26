import gettext

import click

from pulpcore.cli.common.context import (
    PluginRequirement,
    PulpContentContext,
    PulpContext,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import list_command

_ = gettext.gettext


@click.group()
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    """
    Perform actions on all content units.

    Please look for the plugin specific content commands for more detailed actions.
    i.e. 'pulp file content <...>'
    """
    pulp_ctx.needs_plugin(PluginRequirement("core", min="3.10"))
    ctx.obj = PulpContentContext(pulp_ctx)


content.add_command(list_command())
