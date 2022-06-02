import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    destroy_command,
    href_option,
    list_command,
    pulp_group,
    show_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import PulpUploadContext

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def upload(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpUploadContext(pulp_ctx)


lookup_options = [href_option]

upload.add_command(list_command())
upload.add_command(show_command(decorators=lookup_options))
upload.add_command(destroy_command(decorators=lookup_options))
