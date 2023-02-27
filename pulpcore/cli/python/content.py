from typing import IO, Optional, Union

import click
from pulp_glue.common.context import PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpArtifactContext
from pulp_glue.python.context import PulpPythonContentContext, PulpPythonRepositoryContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    chunk_size_option,
    create_command,
    href_option,
    list_command,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    resource_option,
    show_command,
)

translation = get_translation(__name__)
_ = translation.gettext


def _sha256_artifact_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[Union[str, PulpEntityContext]]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx is not None
        return PulpArtifactContext(pulp_ctx, entity={"sha256": value})
    return value


repository_option = resource_option(
    "--repository",
    default_plugin="python",
    default_type="python",
    context_table={
        "python:python": PulpPythonRepositoryContext,
    },
    href_pattern=PulpPythonRepositoryContext.HREF_PATTERN,
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
    type=click.Choice(["package"], case_sensitive=False),
    default="package",
)
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpCLIContext, content_type: str) -> None:
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
@chunk_size_option
@repository_option
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpCLIContext,
    entity_ctx: PulpPythonContentContext,
    relative_path: str,
    file: IO[bytes],
    chunk_size: int,
    repository: Optional[PulpPythonRepositoryContext],
) -> None:
    """Create a Python package content unit through uploading a file"""
    result = entity_ctx.upload(
        relative_path=relative_path, file=file, chunk_size=chunk_size, repository=repository
    )
    pulp_ctx.output_result(result)
