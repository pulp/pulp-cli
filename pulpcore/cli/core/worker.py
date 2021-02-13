import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import href_option, list_command, name_option, show_command
from pulpcore.cli.core.context import PulpWorkerContext


@click.group()
@pass_pulp_context
@click.pass_context
def worker(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpWorkerContext(pulp_ctx)


filter_options = [
    click.option("--name"),
    click.option("--name-contains", "name__contains"),
    click.option("--name-icontains", "name__icontains"),
    click.option("--missing/--not-missing", default=None),
    click.option("--online/--not-online", default=None),
]

worker.add_command(list_command(decorators=filter_options))
worker.add_command(show_command(decorators=[href_option, name_option]))
