from typing import Optional

import click

from pulpcore.cli.common.generic import (
    list_entities,
    show_by_name,
    destroy_by_name,
)
from pulpcore.cli.common.context import (
    pass_pulp_context,
    pass_repository_context,
    PulpContext,
    PulpRepositoryContext,
)
from pulpcore.cli.rpm.context import PulpRpmRemoteContext, PulpRpmRepositoryContext


@click.group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["rpm"], case_sensitive=False),
    default="rpm",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpContext, repo_type: str) -> None:
    if repo_type == "rpm":
        ctx.obj = PulpRpmRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()


repository.add_command(show_by_name)
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
        remote_href: str = PulpRpmRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
        repository["remote"] = remote_href

    result = repository_ctx.create(body=repository)
    pulp_ctx.output_result(result)


@repository.command()
@click.option("--name", required=True)
@click.option("--description")
@click.option("--remote")
@pass_repository_context
@pass_pulp_context
def update(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    name: str,
    description: Optional[str],
    remote: Optional[str],
) -> None:
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
            remote_href: str = PulpRpmRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
            repository["remote"] = remote_href

    repository_ctx.update(repository_href, body=repository)


repository.add_command(destroy_by_name)
repository.add_command(show_by_name)


@repository.command()
@click.option("--name", required=True)
@click.option("--remote")
@pass_repository_context
@pass_pulp_context
def sync(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    name: str,
    remote: Optional[str],
) -> None:
    repository = repository_ctx.find(name=name)
    repository_href = repository["pulp_href"]

    body = {}

    if remote:
        remote_href: str = PulpRpmRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
        body["remote"] = remote_href
    elif repository["remote"] is None:
        raise click.ClickException(
            f"Repository '{name}' does not have a default remote. Please specify with '--remote'."
        )

    repository_ctx.sync(
        href=repository_href,
        body=body,
    )
