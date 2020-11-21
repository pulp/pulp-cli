import click


from pulpcore.cli.common.generic import (
    list_entities,
    show_by_href,
    destroy_by_href,
)
from pulpcore.cli.common.context import (
    pass_pulp_context,
    pass_entity_context,
    PulpContext,
)

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


publication.add_command(list_entities)
publication.add_command(show_by_href)


@publication.command()
@click.option("--repository", required=True)
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext, publication_ctx: PulpFilePublicationContext, repository: str
) -> None:
    repository_href: str = PulpFileRepositoryContext(pulp_ctx).find(name=repository)["pulp_href"]
    body = {"repository": repository_href}
    result = publication_ctx.create(body=body)
    publication = publication_ctx.show(result["created_resources"][0])
    pulp_ctx.output_result(publication)


publication.add_command(destroy_by_href)
