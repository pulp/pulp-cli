from typing import Optional

import click

from pulpcore.cli.ansible.context import (
    PulpAnsibleCollectionRemoteContext,
    PulpAnsibleRepositoryContext,
    PulpAnsibleRoleRemoteContext,
)
from pulpcore.cli.common.context import (
    EntityDefinition,
    PulpContext,
    PulpRepositoryContext,
    pass_pulp_context,
    pass_repository_context,
)
from pulpcore.cli.common.generic import (
    destroy_by_name,
    list_entities,
    show_by_name,
    version_command,
)


@click.group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["ansible"], case_sensitive=False),
    default="ansible",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpContext, repo_type: str) -> None:
    if repo_type == "ansible":
        ctx.obj = PulpAnsibleRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()


repository.add_command(show_by_name)
repository.add_command(list_entities)
repository.add_command(destroy_by_name)
repository.add_command(version_command())


@repository.command()
@click.option("--name", required=True)
@click.option("--description", help="an optional description")
@click.option("--remote", help="an optional remote to default when syncing")
@pass_repository_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    name: str,
    description: Optional[str],
    remote: Optional[str],
) -> None:
    """Creates a repository to store Role and Collection content"""
    repository: EntityDefinition = {"name": name, "description": description}
    if remote is not None:
        try:
            remote_href: str = PulpAnsibleCollectionRemoteContext(pulp_ctx).find(name=remote)[
                "pulp_href"
            ]
        except click.ClickException:
            remote_href = PulpAnsibleRoleRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
        repository["remote"] = remote_href

    result = repository_ctx.create(body=repository)
    pulp_ctx.output_result(result)


@repository.command()
@click.option("--name", required=True)
@click.option("--description", help="new optional description")
@click.option("--remote", help="new optional remote")
@pass_repository_context
@pass_pulp_context
def update(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    name: str,
    description: Optional[str],
    remote: Optional[str],
) -> None:
    """
    The description and remote can both be unset using an empty string

    e.g. pulp ansible repository update --name foo --description ""
    """
    repository: EntityDefinition = repository_ctx.find(name=name)

    if description is not None:
        if description == "":
            # unset the description
            description = None
        if description != repository["description"]:
            repository["description"] = description

    if remote is not None:
        if remote == "":
            # unset the remote
            remote_href: str = ""
        else:
            try:
                remote_href = PulpAnsibleCollectionRemoteContext(pulp_ctx).find(name=remote)[
                    "pulp_href"
                ]
            except click.ClickException:
                remote_href = PulpAnsibleRoleRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]

        repository["remote"] = remote_href

    repository_ctx.update(repository["pulp_href"], body=repository)
    result = repository_ctx.show(repository["pulp_href"])
    pulp_ctx.output_result(result)


@repository.command()
@click.option("--name", required=True)
@click.option("--remote", help="optional remote name to perform sync with")
@pass_repository_context
@pass_pulp_context
def sync(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    name: str,
    remote: Optional[str],
) -> None:
    """
    If remote is not specified sync will try to use the default remote associated with
    the repository
    """
    repository: EntityDefinition = repository_ctx.find(name=name)
    repository_href: str = repository["pulp_href"]
    body: EntityDefinition = dict()

    if remote:
        try:
            remote_href: str = PulpAnsibleCollectionRemoteContext(pulp_ctx).find(name=remote)[
                "pulp_href"
            ]
        except click.ClickException:
            remote_href = PulpAnsibleRoleRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
        body["remote"] = remote_href
    elif repository["remote"] is None:
        raise click.ClickException(
            f"Repository '{name}' does not have a default remote. Please specify with '--remote'."
        )

    repository_ctx.sync(
        href=repository_href,
        body=body,
    )


# TODO Finish 'add' and 'remove' commands when role and collection contexts are implemented
