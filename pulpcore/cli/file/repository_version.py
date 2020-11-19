import click

from pulpcore.cli.common import (
    list_entities,
    show_version,
    destroy_version,
    pass_pulp_context,
    pass_repository_context,
    PulpContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)
from pulpcore.cli.file.repository import PulpFileRepositoryContext


class PulpFileRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF: str = "file_file_repository_version_href"
    REPOSITORY_HREF: str = "file_file_repository_href"
    LIST_ID: str = "repositories_file_file_versions_list"
    READ_ID: str = "repositories_file_file_versions_read"
    DELETE_ID: str = "repositories_file_file_versions_delete"


@click.group()
@click.option("--repository", required=True)
@pass_repository_context
@pass_pulp_context
@click.pass_context
def version(
    ctx: click.Context,
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    repository: str,
) -> None:
    # Maybe we can get this relationship being presented on the RepositoryContext class
    if isinstance(repository_ctx, PulpFileRepositoryContext):
        ctx.obj = PulpFileRepositoryVersionContext(pulp_ctx)
    else:
        raise NotImplementedError()
    ctx.obj.repository = repository_ctx.find(name=repository)


version.add_command(list_entities)
version.add_command(show_version)
version.add_command(destroy_version)
