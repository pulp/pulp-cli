import click


from pulpcore.cli.common import (
    show_by_href,
    destroy_by_href,
    limit_option,
    offset_option,
    PulpContext,
    PulpEntityContext,
)

from pulpcore.cli.file.repository import PulpFileRepositoryContext


class PulpFilePublicationContext(PulpEntityContext):
    ENTITY: str = "publication"
    HREF: str = "file_file_publication_href"
    LIST_ID: str = "publications_file_file_list"
    READ_ID: str = "publications_file_file_read"
    CREATE_ID: str = "publications_file_file_create"
    DELETE_ID: str = "publications_file_file_delete"


@click.group()
@click.option(
    "-t",
    "--type",
    "publication_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@click.pass_context
def publication(ctx: click.Context, publication_type: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)

    if publication_type == "file":
        ctx.obj = PulpFilePublicationContext(pulp_ctx)
    else:
        raise NotImplementedError()


@publication.command()
@limit_option
@offset_option
@click.pass_context
def list(ctx: click.Context, limit: int, offset: int) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    publication_ctx: PulpFilePublicationContext = ctx.find_object(PulpFilePublicationContext)

    result = publication_ctx.list(limit=limit, offset=offset, parameters={})
    pulp_ctx.output_result(result)


publication.add_command(show_by_href)


@publication.command()
@click.option("--repository", required=True)
@click.pass_context
def create(ctx: click.Context, repository: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    publication_ctx: PulpFilePublicationContext = ctx.find_object(PulpFilePublicationContext)

    repository_href: str = PulpFileRepositoryContext(pulp_ctx).find(name=repository)["pulp_href"]
    body = {"repository": repository_href}
    result = publication_ctx.create(body=body)
    publication = publication_ctx.show(result["created_resources"][0])
    pulp_ctx.output_result(publication)


publication.add_command(destroy_by_href)
