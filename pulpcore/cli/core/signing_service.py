import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpSigningServiceContext

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
def signing_service(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpSigningServiceContext(pulp_ctx)


signing_service_filter = [
    click.option("--name"),
]


lookup_options = [
    name_option,
    href_option,
]

signing_service.add_command(list_command(decorators=signing_service_filter))
signing_service.add_command(show_command(decorators=lookup_options))
