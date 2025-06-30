import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpUploadContext

from pulp_cli.generic import (
    PulpCLIContext,
    destroy_command,
    href_option,
    list_command,
    pass_pulp_context,
    pulp_group,
    resource_lookup_option,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def upload(ctx: click.Context, pulp_ctx: PulpCLIContext, /) -> None:
    ctx.obj = PulpUploadContext(pulp_ctx)


upload_lookup_option = resource_lookup_option(
    "--upload",
    lookup_key=None,
    context_class=PulpUploadContext,
)
lookup_options = [href_option, upload_lookup_option]

upload.add_command(list_command())
upload.add_command(show_command(decorators=lookup_options))
upload.add_command(destroy_command(decorators=lookup_options))
