import gettext
from typing import IO, Optional, Union

import click

from pulpcore.cli.common.context import (
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import create_command, href_option, list_command, show_command
from pulpcore.cli.core.context import PulpArtifactContext
from pulpcore.cli.python.context import PulpPythonContentContext

_ = gettext.gettext


def _sha256_artifact_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[Union[str, PulpEntityContext]]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx: PulpContext = ctx.find_object(PulpContext)
        return PulpArtifactContext(pulp_ctx, entity={"sha256": value})
    return value


@click.group()
@click.option(
    "-t",
    "--type",
    "content_type",
    type=click.Choice(["package"], case_sensitive=False),
    default="package",
)
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpContext, content_type: str) -> None:
    if content_type == "package":
        ctx.obj = PulpPythonContentContext(pulp_ctx)
    else:
        raise NotImplementedError()


create_options = [
    click.option("--relative-path", required=True, help=_("Exact name of file")),
    click.option(
        "--sha256",
        "artifact",
        required=True,
        help=_("Digest of the artifact to use"),
        callback=_sha256_artifact_callback,
    ),
]
content.add_command(
    list_command(
        decorators=[
            click.option("--filename", type=str),
        ]
    )
)
content.add_command(show_command(decorators=[href_option]))
content.add_command(create_command(decorators=create_options))


@content.command()
@click.option("--relative-path", required=True, help=_("Exact name of file"))
@click.option("--file", type=click.File("rb"), required=True, help=_("Path to file"))
@click.option(
    "--chunk-size", default=1000000, type=int, help=_("Chunk size in bytes (default is 1 MB)")
)
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpContext,
    entity_ctx: PulpPythonContentContext,
    relative_path: str,
    file: IO[bytes],
    chunk_size: int,
) -> None:
    """Create a Python package content unit through uploading a file"""
    artifact_href = PulpArtifactContext(pulp_ctx).upload(file, chunk_size)
    content = {"relative_path": relative_path, "artifact": artifact_href}
    result = entity_ctx.create(body=content)
    pulp_ctx.output_result(result)
