import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpWorkerContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    href_option,
    list_command,
    name_option,
    pass_pulp_context,
    pulp_group,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def worker(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
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
