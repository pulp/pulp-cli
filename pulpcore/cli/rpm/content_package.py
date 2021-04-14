import gettext
from typing import IO, Optional, Union

import click

from pulpcore.cli.common.context import (
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import create_command, href_option, list_command, show_command, destroy_command
from pulpcore.cli.core.context import PulpArtifactContext
from pulpcore.cli.rpm.context import PulpRpmPackageContentContext

_ = gettext.gettext


@click.group()
@pass_pulp_context
@click.pass_context
def content_package(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpRpmPackageContentContext(pulp_ctx)


content_package.add_command(
    list_command(
        decorators=[
            click.option("--arch", type=str),
            click.option("--arch-in", "arch__in",  type=str),
            click.option("--epoch", type=str),
            click.option("--epoch-in", "epoch__in", type=str),
            click.option("--fields", type=str),
            click.option("--name", type=str),
            click.option("--name-in", "name__in", type=str),
            click.option("--release", type=str),
            click.option("--release-in", "release__in", type=str),
            click.option("--version", type=str),
            click.option("--version-in", "version__in", type=str),
            click.option("--repository-version", type=str),
        ]
    )
)
content_package.add_command(show_command(decorators=[href_option]))

@content_package.command()
@click.option("--relative-path", required=True, help=_("Exact name of rpm"))
@click.option("--file", type=click.File("rb"), required=True, help=_("Path to file"))
@click.option(
    "--chunk-size", default=1000000, type=int, help=_("Chunk size in bytes (default is 1 MB)")
)
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpContext,
    entity_ctx: PulpRpmPackageContentContext,
    relative_path: str,
    file: IO[bytes],
    chunk_size: int,
) -> None:
    """Create a Rpm package content unit through uploading a file"""
    artifact_href = PulpArtifactContext(pulp_ctx).upload(file, chunk_size)
    content_package = {"relative_path": relative_path, "artifact": artifact_href}
    result = entity_ctx.create(body=content_package)
    pulp_ctx.output_result(result)
