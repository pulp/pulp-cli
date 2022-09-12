import os
from typing import IO, Any, Dict, Optional, Union

import click

from pulpcore.cli.common.context import (
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
    PulpRepositoryContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import (
    chunk_size_option,
    create_command,
    href_option,
    list_command,
    pulp_group,
    resource_option,
    show_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import PulpArtifactContext, PulpUploadContext
from pulpcore.cli.file.context import PulpFileContentContext, PulpFileRepositoryContext

translation = get_translation(__name__)
_ = translation.gettext


def _relative_path_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.entity = {"relative_path": value}
    return value


def _sha256_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.entity = {"sha256": value}
    return value


def _sha256_artifact_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[Union[str, PulpEntityContext]]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx = ctx.find_object(PulpContext)
        assert pulp_ctx is not None
        return PulpArtifactContext(pulp_ctx, entity={"sha256": value})
    return value


repository_option = resource_option(
    "--repository",
    default_plugin="file",
    default_type="file",
    context_table={
        "file:file": PulpFileRepositoryContext,
    },
    href_pattern=PulpRepositoryContext.HREF_PATTERN,
    help=_(
        "Repository to add the content to in the form '[[<plugin>:]<resource_type>:]<name>' or by "
        "href."
    ),
)


@pulp_group()
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


lookup_options = [
    href_option,
    click.option("--relative-path", callback=_relative_path_callback, expose_value=False),
    click.option("--sha256", callback=_sha256_callback, expose_value=False),
]
create_options = [
    click.option("--relative-path", required=True),
    click.option(
        "--sha256",
        "artifact",
        required=True,
        help=_("Digest of the artifact to use"),
        callback=_sha256_artifact_callback,
    ),
    repository_option,
]

content.add_command(
    list_command(
        decorators=[
            click.option("--relative-path"),
            click.option("--sha256"),
        ]
    )
)
content.add_command(show_command(decorators=lookup_options))
content.add_command(create_command(decorators=create_options))


@content.command()
@click.option("--relative-path", required=True)
@click.option("--file", type=click.File("rb"), required=True)
@chunk_size_option
@repository_option
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpContext,
    entity_ctx: PulpFileContentContext,
    relative_path: str,
    file: IO[bytes],
    chunk_size: int,
    repository: Optional[PulpEntityContext],
) -> None:
    """Create a file content unit by uploading a file"""
    size = os.path.getsize(file.name)
    body: Dict[str, Any] = {"relative_path": relative_path}
    uploads: Dict[str, IO[bytes]] = {}
    if chunk_size > size:
        uploads["file"] = file
    elif pulp_ctx.has_plugin(PluginRequirement("core", min="3.20.0")):
        upload_href = PulpUploadContext(pulp_ctx).upload_file(file, chunk_size)
        body["upload"] = upload_href
    else:
        artifact_href = PulpArtifactContext(pulp_ctx).upload(file, chunk_size)
        body["artifact"] = artifact_href
    if repository:
        body["repository"] = repository
    result = entity_ctx.create(body=body, uploads=uploads)
    pulp_ctx.output_result(result)
