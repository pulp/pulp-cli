from typing import Optional

import click

from pulpcore.cli.common import (
    destroy_by_name,
    limit_option,
    offset_option,
    PulpContext,
    PulpEntityContext,
)
from pulpcore.cli.container.remote import PulpContainerRemoteContext


class PulpContainerRepositoryContext(PulpEntityContext):
    ENTITY: str = "repository"
    HREF: str = "container_container_repository_href"
    LIST_ID: str = "repositories_container_container_list"
    CREATE_ID: str = "repositories_container_container_create"
    UPDATE_ID: str = "repositories_container_container_update"
    DELETE_ID: str = "repositories_container_container_delete"
    SYNC_ID: str = "repositories_container_container_sync"


@click.group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["container"], case_sensitive=False),
    default="container",
)
@click.pass_context
def repository(ctx: click.Context, repo_type: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)

    if repo_type == "container":
        ctx.obj = PulpContainerRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()


@repository.command()
@limit_option
@offset_option
@click.pass_context
def list(ctx: click.Context, limit: int, offset: int) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    repository_ctx: PulpContainerRepositoryContext = ctx.find_object(PulpContainerRepositoryContext)

    result = repository_ctx.list(limit=limit, offset=offset, parameters={})
    pulp_ctx.output_result(result)


@repository.command()
@click.option("--name", required=True)
@click.option("--description")
@click.option("--remote")
@click.pass_context
def create(
    ctx: click.Context, name: str, description: Optional[str], remote: Optional[str]
) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    repository_ctx: PulpContainerRepositoryContext = ctx.find_object(PulpContainerRepositoryContext)

    repository = {"name": name, "description": description}
    if remote:
        remote_href: str = PulpContainerRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
        repository["remote"] = remote_href

    result = repository_ctx.create(body=repository)
    pulp_ctx.output_result(result)


@repository.command()
@click.option("--name", required=True)
@click.option("--description")
@click.option("--remote")
@click.pass_context
def update(
    ctx: click.Context, name: str, description: Optional[str], remote: Optional[str]
) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    repository_ctx: PulpContainerRepositoryContext = ctx.find_object(PulpContainerRepositoryContext)

    repository = repository_ctx.find(name=name)
    repository_href = repository["pulp_href"]

    if description is not None:
        if description == "":
            # unset the description
            description = None
        if description != repository["description"]:
            repository["description"] = description

    if remote is not None:
        if remote == "":
            # unset the remote
            repository["remote"] = ""
        elif remote:
            remote_href: str = PulpContainerRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
            repository["remote"] = remote_href

    repository_ctx.update(repository_href, body=repository)


repository.add_command(destroy_by_name)


@repository.command()
@click.option("--name", required=True)
@click.option("--remote")
@click.pass_context
def sync(ctx: click.Context, name: str, remote: Optional[str]) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    repository_ctx: PulpContainerRepositoryContext = ctx.find_object(PulpContainerRepositoryContext)

    repository = repository_ctx.find(name=name)
    repository_href = repository["pulp_href"]

    body = {}

    if remote:
        remote_href: str = PulpContainerRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
        body["remote"] = remote_href
    elif repository["remote"] is None:
        raise click.ClickException(
            f"Repository '{name}' does not have a default remote. Please specify with '--remote'."
        )

    pulp_ctx.call(
        repository_ctx.SYNC_ID,
        parameters={repository_ctx.HREF: repository_href},
        body=body,
    )
