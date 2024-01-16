import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpUploadContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    destroy_command,
    href_option,
    list_command,
    pass_pulp_context,
    pulp_group,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def upload(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpUploadContext(pulp_ctx)


lookup_options = [href_option]

upload.add_command(list_command())
upload.add_command(show_command(decorators=lookup_options))
upload.add_command(destroy_command(decorators=lookup_options))
