import click

from pulpcore.cli.common.context import PulpRepositoryContext
from pulpcore.cli.common.generic import (
    PulpCLIContext,
    list_command,
    name_filter_options,
    pass_pulp_context,
    pulp_group,
)
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    """
    Perform actions on all repositories.

    Please look for the plugin specific repository commands for more detailed actions.
    i.e. 'pulp file repository <...>'
    """
    ctx.obj = PulpRepositoryContext(pulp_ctx)


filter_options = name_filter_options

repository.add_command(list_command(decorators=filter_options))
