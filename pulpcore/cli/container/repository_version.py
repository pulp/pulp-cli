import click

from pulpcore.cli.common import (
    limit_option,
    offset_option,
    pass_pulp_context,
    pass_entity_context,
    pass_repository_context,
    PulpContext,
    PulpRepositoryContext,
    PulpEntityContext,
)
from pulpcore.cli.container.repository import (
    PulpContainerRepositoryContext,
    PulpContainerPushRepositoryContext,
)


class PulpContainerRepositoryVersionContext(PulpEntityContext):
    ENTITY: str = "repository version"
    HREF: str = "container_container_repository_version_href"
    LIST_ID: str = "repositories_container_container_versions_list"
    READ_ID: str = "repositories_container_container_versions_read"
    DELETE_ID: str = "repositories_container_container_versions_delete"


class PulpContainerPushRepositoryVersionContext(PulpEntityContext):
    ENTITY: str = "repository version"
    HREF: str = "container_container_push_repository_version_href"
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
        ctx.obj = PulpContainerRepositoryVersionContext(pulp_ctx)
    else:
        raise NotImplementedError()
    repository_ctx.entity = repository_ctx.find(name=repository)


@version.command()
@limit_option
@offset_option
@pass_entity_context
@pass_repository_context
@pass_pulp_context
def list(
    pulp_ctx: PulpContext,
    repository_ctx: PulpContainerRepositoryContext,
    repository_version_ctx: PulpContainerRepositoryVersionContext,
    limit: int,
    offset: int,
) -> None:
    repo_href = repository_ctx.entity["pulp_href"]
    result = repository_version_ctx.list(
        limit=limit, offset=offset, parameters={"container_container_repository_href": repo_href}
    )
    pulp_ctx.output_result(result)


@version.command()
@click.option("--version", required=True, type=int)
@pass_entity_context
@pass_repository_context
@pass_pulp_context
def destroy(
    pulp_ctx: PulpContext,
    repository_ctx: PulpContainerRepositoryContext,
    repository_version_ctx: PulpContainerRepositoryVersionContext,
    version: int,
) -> None:
    repo_href = repository_ctx.entity["pulp_href"]
    repo_version_href = f"{repo_href}versions/{version}"
    result = repository_version_ctx.delete(repo_version_href)
    pulp_ctx.output_result(result)
