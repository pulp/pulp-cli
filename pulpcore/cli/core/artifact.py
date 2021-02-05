import gettext
from copy import deepcopy
from typing import IO

import click

from pulpcore.cli.common.context import PulpContext, pass_entity_context, pass_pulp_context
from pulpcore.cli.common.generic import list_entities, show_by_href
from pulpcore.cli.core.context import PulpArtifactContext

_ = gettext.gettext


@click.group()
@pass_pulp_context
@click.pass_context
def artifact(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpArtifactContext(pulp_ctx)


# deepcopy to not effect other list subcommands
list_artifacts = deepcopy(list_entities)
click.option("--sha256")(list_artifacts)
artifact.add_command(list_artifacts)

artifact.add_command(show_by_href)


@artifact.command()
@click.option("--file", type=click.File("rb"), required=True)
@click.option(
    "--chunk-size", default=1000000, type=int, help=_("Chunk size in bytes (default is 1 MB)")
)
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
