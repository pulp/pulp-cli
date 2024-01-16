import click
from pulp_glue.common.context import PulpContentContext
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import PulpCLIContext, list_command, pass_pulp_context, pulp_group

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    """
    Perform actions on all content units.

    Please look for the plugin specific content commands for more detailed actions.
    i.e. 'pulp file content <...>'
    """
    ctx.obj = PulpContentContext(pulp_ctx)


content.add_command(list_command())
