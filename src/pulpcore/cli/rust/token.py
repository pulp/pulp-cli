import click

from pulp_glue.common.i18n import get_translation
from pulp_glue.rust.context import PulpRustCargoTokenContext

from pulp_cli.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    href_option,
    list_command,
    name_option,
    pass_pulp_context,
    pulp_group,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext

lookup_options = [href_option, name_option]
create_options = [
    click.option("--name", required=True, help=_("Name of the token")),
]


@pulp_group(name="token")
@pass_pulp_context
@click.pass_context
def token(ctx: click.Context, pulp_ctx: PulpCLIContext, /) -> None:
    ctx.obj = PulpRustCargoTokenContext(pulp_ctx)


token.add_command(list_command())
token.add_command(show_command(decorators=lookup_options))
token.add_command(create_command(decorators=create_options))
token.add_command(destroy_command(decorators=lookup_options))
