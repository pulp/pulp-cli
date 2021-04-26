import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import href_option, list_command, show_command
from pulpcore.cli.core.context import PulpTaskGroupContext

_ = gettext.gettext


@click.group()
@pass_pulp_context
@click.pass_context
def task_group(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpTaskGroupContext(pulp_ctx)


task_group.add_command(list_command())
task_group.add_command(show_command(decorators=[href_option]))
