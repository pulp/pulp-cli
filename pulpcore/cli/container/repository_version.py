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
from pulpcore.cli.container.repository import (
    PulpContainerRepositoryContext,
    PulpContainerPushRepositoryContext,
)


class PulpContainerRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF: str = "container_container_repository_version_href"
    REPOSITORY_HREF: str = "container_container_repository_href"
    LIST_ID: str = "repositories_container_container_versions_list"
    READ_ID: str = "repositories_container_container_versions_read"
    DELETE_ID: str = "repositories_container_container_versions_delete"


class PulpContainerPushRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF: str = "container_container_push_repository_version_href"
    REPOSITORY_HREF: str = "container_container_push_repository_href"
    LIST_ID: str = "repositories_container_container_push_versions_list"
    READ_ID: str = "repositories_container_container_push_versions_read"
    DELETE_ID: str = "repositories_container_container_push_versions_delete"


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
    if isinstance(repository_ctx, PulpContainerRepositoryContext):
        ctx.obj = PulpContainerRepositoryVersionContext(pulp_ctx)
    elif isinstance(repository_ctx, PulpContainerPushRepositoryContext):
        ctx.obj = PulpContainerPushRepositoryVersionContext(pulp_ctx)
    else:
        raise NotImplementedError()
    ctx.obj.repository = repository_ctx.find(name=repository)


version.add_command(list_entities)
version.add_command(show_version)
version.add_command(destroy_version)
