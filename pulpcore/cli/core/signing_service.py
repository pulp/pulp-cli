import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import href_option, list_command, name_option, show_command
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import PulpSigningServiceContext

translation = get_translation(__name__)
_ = translation.gettext


@click.group()
@pass_pulp_context
@click.pass_context
def signing_service(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpSigningServiceContext(pulp_ctx)


lookup_options = [
    name_option,
    href_option,
]

signing_service.add_command(list_command())
signing_service.add_command(show_command(decorators=lookup_options))
