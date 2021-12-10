from typing import IO

import click

from pulpcore.cli.common.context import PulpContext, pass_entity_context, pass_pulp_context
from pulpcore.cli.common.generic import chunk_size_option, href_option, list_command, show_command
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import PulpArtifactContext

translation = get_translation(__name__)
_ = translation.gettext


@click.group()
@pass_pulp_context
@click.pass_context
def artifact(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpArtifactContext(pulp_ctx)


filter_options = [click.option("--sha256")]
lookup_options = [href_option]

artifact.add_command(list_command(decorators=filter_options))
artifact.add_command(show_command(decorators=lookup_options))


@artifact.command()
@click.option("--file", type=click.File("rb"), required=True)
@chunk_size_option
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpContext,
    artifact_ctx: PulpArtifactContext,
    file: IO[bytes],
    chunk_size: int,
) -> None:
    artifact_href = artifact_ctx.upload(file, chunk_size)
    result = artifact_ctx.show(artifact_href)
    pulp_ctx.output_result(result)
