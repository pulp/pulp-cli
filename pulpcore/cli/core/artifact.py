import typing as t

import click
from pulp_glue.common.context import PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpArtifactContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    chunk_size_option,
    href_option,
    list_command,
    lookup_callback,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def artifact(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpArtifactContext(pulp_ctx)


filter_options = [
    click.option("--md5"),
    click.option("--sha1"),
    click.option("--sha224"),
    click.option("--sha256"),
    click.option("--sha384"),
    click.option("--sha512"),
]
lookup_options = [
    href_option,
    click.option("--md5", callback=lookup_callback("md5", PulpArtifactContext), expose_value=False),
    click.option(
        "--sha1", callback=lookup_callback("sha1", PulpArtifactContext), expose_value=False
    ),
    click.option(
        "--sha224", callback=lookup_callback("sha224", PulpArtifactContext), expose_value=False
    ),
    click.option(
        "--sha256", callback=lookup_callback("sha256", PulpArtifactContext), expose_value=False
    ),
    click.option(
        "--sha384", callback=lookup_callback("sha384", PulpArtifactContext), expose_value=False
    ),
    click.option(
        "--sha512", callback=lookup_callback("sha512", PulpArtifactContext), expose_value=False
    ),
]

artifact.add_command(list_command(decorators=filter_options))
artifact.add_command(show_command(decorators=lookup_options))


@artifact.command()
@click.option("--file", type=click.File("rb"), required=True)
@chunk_size_option
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpCLIContext,
    artifact_ctx: PulpEntityContext,
    file: t.IO[bytes],
    chunk_size: int,
) -> None:
    assert isinstance(artifact_ctx, PulpArtifactContext)

    artifact_ctx.upload(file, chunk_size)
    pulp_ctx.output_result(artifact_ctx.entity)
