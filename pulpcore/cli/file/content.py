from typing import IO

from copy import deepcopy
import click

from pulpcore.cli.common.generic import (
    list_entities,
    show_by_href,
)
from pulpcore.cli.common.context import (
    PulpContext,
    pass_pulp_context,
    pass_entity_context,
)
from pulpcore.cli.core.context import PulpArtifactContext
from pulpcore.cli.file.context import PulpFileContentContext


@click.group()
@click.option(
    "-t",
    "--type",
    "content_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpContext, content_type: str) -> None:
    if content_type == "file":
        ctx.obj = PulpFileContentContext(pulp_ctx)
    else:
        raise NotImplementedError()


# deepcopy to not effect other list subcommands
list_content = deepcopy(list_entities)
click.option("--relative-path", type=str)(list_content)
click.option("--sha256", type=str)(list_content)
content.add_command(list_content)

content.add_command(show_by_href)


@content.command()
@click.option("--relative-path", required=True)
@click.option("--sha256", required=True, help="Digest of the artifact to use")
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    entity_ctx: PulpFileContentContext,
    relative_path: str,
    sha256: str,
) -> None:
    """Create a file content unit from an existing artifact"""
    artifact = PulpArtifactContext(pulp_ctx).find(sha256=sha256)
    content = {"relative_path": relative_path, "artifact": artifact["pulp_href"]}
    task = entity_ctx.create(body=content)
    result = entity_ctx.show(task["created_resources"][0])
    pulp_ctx.output_result(result)


@content.command()
@click.option("--relative-path", required=True)
@click.option("--file", type=click.File("rb"), required=True)
@click.option(
    "--chunk-size", default=1000000, type=int, help="Chunk size in bytes (default is 1 MB)"
)
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpContext,
    entity_ctx: PulpFileContentContext,
    relative_path: str,
    file: IO[bytes],
    chunk_size: int,
) -> None:
    """Create a file content unit by uploading a file"""
    artifact_href = PulpArtifactContext(pulp_ctx).upload(file, chunk_size)
    content = {"relative_path": relative_path, "artifact": artifact_href}
    task = entity_ctx.create(body=content)
    result = entity_ctx.show(task["created_resources"][0])
    pulp_ctx.output_result(result)
