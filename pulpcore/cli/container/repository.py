from typing import Any, Optional, cast

import click

from pulpcore.cli.common.generic import (
    list_entities,
    show_entity,
    destroy_entity,
)
from pulpcore.cli.common.context import (
    pass_pulp_context,
    pass_repository_context,
    PulpContext,
    PulpRepositoryContext,
)
from pulpcore.cli.container.context import (
    PulpContainerRemoteContext,
    PulpContainerRepositoryContext,
    PulpContainerPushRepositoryContext,
)


def _type_callback(ctx: click.Context, param: Any, value: str) -> str:
    group: click.Group = cast(click.Group, ctx.command)
    # Push repositories cannot be manipulated directly
    if value == "push":
        group.commands.pop("create", None)
        group.commands.pop("update", None)
        group.commands.pop("destroy", None)
        group.commands.pop("sync", None)
        group.commands.pop("add", None)
        group.commands.pop("remove", None)
    return value


def _name_callback(ctx: click.Context, param: Any, value: str) -> str:
    group: click.Group = cast(click.Group, ctx.command)
    if value is not None:
        group.commands.pop("list", None)
    else:
        group.commands.pop("show", None)
        group.commands.pop("version", None)
    return value


@click.group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["container", "push"], case_sensitive=False),
    default="container",
    callback=_type_callback,
    is_eager=True,
)
@click.option("--name", type=str, callback=_name_callback, is_eager=True)
@pass_pulp_context
@click.pass_context
def repository(
    ctx: click.Context,
    pulp_ctx: PulpContext,
    repo_type: str,
    name: Optional[str],
) -> None:
    if repo_type == "container":
        ctx.obj = PulpContainerRepositoryContext(pulp_ctx)
    elif repo_type == "push":
        ctx.obj = PulpContainerPushRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()

    if name is not None:
        ctx.obj.entity = ctx.obj.find(name=name)


repository.add_command(show_entity)
repository.add_command(list_entities)


@repository.command()
@click.option("--name", required=True)
@click.option("--description")
@click.option("--remote")
@pass_repository_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    name: str,
    description: Optional[str],
    remote: Optional[str],
) -> None:
    repository = {"name": name, "description": description}
    if remote:
        remote_href: str = PulpContainerRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
        repository["remote"] = remote_href

    result = repository_ctx.create(body=repository)
    pulp_ctx.output_result(result)


@repository.command()
@click.option("--description")
@click.option("--remote")
@pass_repository_context
@pass_pulp_context
def update(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    description: Optional[str],
    remote: Optional[str],
) -> None:
    repository = repository_ctx.entity
    assert repository is not None
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


repository.add_command(destroy_entity)


@repository.command()
@click.option("--remote")
@pass_repository_context
@pass_pulp_context
def sync(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    remote: Optional[str],
) -> None:
    assert repository_ctx.SYNC_ID is not None

    repository = repository_ctx.entity
    assert repository is not None
    repository_href = repository["pulp_href"]

    body = {}

    if remote:
        remote_href: str = PulpContainerRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
        body["remote"] = remote_href
    elif repository["remote"] is None:
        name = repository["name"]
        raise click.ClickException(
            f"Repository '{name}' does not have a default remote. Please specify with '--remote'."
        )

    repository_ctx.sync(
        href=repository_href,
        body=body,
    )
