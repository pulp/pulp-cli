import click

from pulpcore.cli.common.context import PulpContext, PulpRepositoryContext, pass_pulp_context
from pulpcore.cli.common.generic import list_command
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


@click.group()
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    """
    Perform actions on all repositories.

    Please look for the plugin specific repository commands for more detailed actions.
    i.e. 'pulp file repository <...>'
    """
    ctx.obj = PulpRepositoryContext(pulp_ctx)


filter_options = [
    click.option("--name"),
    click.option(
        "--name-contains",
        "name__contains",
    ),
    click.option(
        "--name-icontains",
        "name__icontains",
    ),
    click.option(
        "--name-in",
        "name__in",
    ),
]

repository.add_command(list_command(decorators=filter_options))
