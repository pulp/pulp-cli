import click

from pulpcore.cli.common import limit_option, offset_option, PulpContext, PulpEntityContext
from pulpcore.cli.container.repository import PulpContainerRepositoryContext


class PulpContainerRepositoryVersionContext(PulpEntityContext):
    ENTITY: str = "repository version"
    HREF: str = "container_container_repository_version_href"
    LIST_ID: str = "repositories_container_container_versions_list"
    DELETE_ID: str = "repositories_container_container_versions_delete"


@click.group()
@click.pass_context
def version(ctx: click.Context) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)

    # TODO Deduce from PulpRepositoryContext
    if ctx.parent and ctx.parent.params["repo_type"] == "container":
        ctx.obj = PulpContainerRepositoryVersionContext(pulp_ctx)
    else:
        raise NotImplementedError()


@version.command()
@click.option("--repository", required=True)
@limit_option
@offset_option
@click.pass_context
def list(ctx: click.Context, repository: str, limit: int, offset: int) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    repository_ctx: PulpContainerRepositoryContext = ctx.find_object(PulpContainerRepositoryContext)
    repository_version_ctx: PulpContainerRepositoryVersionContext = ctx.find_object(
        PulpContainerRepositoryVersionContext
    )

    repo_href = repository_ctx.find(name=repository)["pulp_href"]
    result = repository_version_ctx.list(
        limit=limit, offset=offset, parameters={"container_container_repository_href": repo_href}
    )
    pulp_ctx.output_result(result)


@version.command()
@click.option("--repository", required=True)
@click.option("--version", required=True, type=int)
@click.pass_context
def destroy(ctx: click.Context, repository: str, version: int) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    repository_ctx: PulpContainerRepositoryContext = ctx.find_object(PulpContainerRepositoryContext)
    repository_version_ctx: PulpContainerRepositoryVersionContext = ctx.find_object(
        PulpContainerRepositoryVersionContext
    )

    repo_href = repository_ctx.find(name=repository)["pulp_href"]
    repo_version_href = f"{repo_href}versions/{version}"
    result = repository_version_ctx.delete(repo_version_href)
    pulp_ctx.output_result(result)
