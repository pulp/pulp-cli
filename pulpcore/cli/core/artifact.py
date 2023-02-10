from typing import IO

import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpArtifactContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    chunk_size_option,
    href_option,
    list_command,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    show_command,
)

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def artifact(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
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
    pulp_ctx: PulpCLIContext,
    artifact_ctx: PulpArtifactContext,
    file: IO[bytes],
    chunk_size: int,
) -> None:
    artifact_ctx.upload(file, chunk_size)
    pulp_ctx.output_result(artifact_ctx.entity)
