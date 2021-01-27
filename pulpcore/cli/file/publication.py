from typing import Optional

import click

from pulpcore.cli.common.context import PulpContext, pass_entity_context, pass_pulp_context
from pulpcore.cli.common.generic import destroy_command, href_option, list_command, show_command
from pulpcore.cli.file.context import PulpFilePublicationContext, PulpFileRepositoryContext


@click.group()
@click.option(
    "-t",
    "--type",
    "publication_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@pass_pulp_context
@click.pass_context
def publication(ctx: click.Context, pulp_ctx: PulpContext, publication_type: str) -> None:
    if publication_type == "file":
        ctx.obj = PulpFilePublicationContext(pulp_ctx)
    else:
        raise NotImplementedError()


publication.add_command(list_command())
publication.add_command(show_command(decorators=[href_option]))
publication.add_command(destroy_command(decorators=[href_option]))


@publication.command()
@click.option("--repository", required=True)
@click.option("--version", type=int, help="a repository version number, leave blank for latest")
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    publication_ctx: PulpFilePublicationContext,
    repository: str,
    version: Optional[int],
) -> None:
    repository_href: str = PulpFileRepositoryContext(
        pulp_ctx, entity={"name": repository}
    ).pulp_href
    if version is not None:
        body = {"repository_version": f"{repository_href}versions/{version}/"}
    else:
        body = {"repository": repository_href}
    result = publication_ctx.create(body=body)
    publication = publication_ctx.show(result["created_resources"][0])
    pulp_ctx.output_result(publication)
