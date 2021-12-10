import click

from pulpcore.cli.common.context import PulpContentContext, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import list_command
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


@click.group()
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    """
    Perform actions on all content units.

    Please look for the plugin specific content commands for more detailed actions.
    i.e. 'pulp file content <...>'
    """
    ctx.obj = PulpContentContext(pulp_ctx)


content.add_command(list_command())
