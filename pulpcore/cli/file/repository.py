from typing import Optional

import click

from pulpcore.cli.common.generic import (
    CondGroup,
    list_command,
    show_command,
    destroy_command,
    version_command,
)
from pulpcore.cli.common.context import (
    pass_pulp_context,
    pass_repository_context,
    PulpContext,
    PulpRepositoryContext,
)
from pulpcore.cli.file.context import (
    PulpFileContentContext,
    PulpFileRemoteContext,
    PulpFileRepositoryContext,
)


def _is_collection_cmd(ctx: click.Context) -> bool:
    return ctx.params.get("name") is None


def _is_entity_cmd(ctx: click.Context) -> bool:
    return ctx.params.get("name") is not None


@click.group(cls=CondGroup)
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
    is_eager=True,
)
@click.option("--name", type=str, is_eager=True)
@pass_pulp_context
@click.pass_context
def repository(
    ctx: click.Context,
    pulp_ctx: PulpContext,
    repo_type: str,
    name: Optional[str],
) -> None:
    if repo_type == "file":
        ctx.obj = PulpFileRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()

    if name is not None:
        ctx.obj.entity = {"name": name}


repository.add_command(list_command(condition=_is_collection_cmd))
repository.add_command(show_command(condition=_is_entity_cmd))
repository.add_command(destroy_command(condition=_is_entity_cmd))
repository.add_command(version_command(condition=_is_entity_cmd))


@repository.command(condition=_is_collection_cmd)
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
        remote_href: str = PulpFileRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
        repository["remote"] = remote_href

    result = repository_ctx.create(body=repository)
    pulp_ctx.output_result(result)


@repository.command(condition=_is_entity_cmd)
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
            remote_href: str = PulpFileRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
            repository["remote"] = remote_href

    repository_ctx.update(repository_href, body=repository)


@repository.command(condition=_is_entity_cmd)
@click.option("--remote")
@pass_repository_context
@pass_pulp_context
def sync(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    remote: Optional[str],
) -> None:
    repository = repository_ctx.entity
    assert repository is not None
    repository_href = repository["pulp_href"]

    body = {}

    if remote:
        remote_href: str = PulpFileRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
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


@repository.command(condition=_is_entity_cmd)
@click.option("--sha256", required=True)
@click.option("--relative-path", required=True)
@click.option("--base-version", type=int)
@pass_repository_context
@pass_pulp_context
def add(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    sha256: str,
    relative_path: str,
    base_version: Optional[int],
) -> None:
    repository = repository_ctx.entity
    assert repository is not None
    repository_href = repository["pulp_href"]

    base_version_href: Optional[str]
    if base_version is not None:
        base_version_href = f"{repository_href}versions/{base_version}/"
    else:
        base_version_href = None

    content_href = PulpFileContentContext(pulp_ctx).find(
        sha256=sha256, relative_path=relative_path
    )["pulp_href"]

    repository_ctx.modify(
        href=repository_href,
        add_content=[content_href],
        base_version=base_version_href,
    )


@repository.command(condition=_is_entity_cmd)
@click.option("--sha256", required=True)
@click.option("--relative-path", required=True)
@click.option("--base-version", type=int)
@pass_repository_context
@pass_pulp_context
def remove(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    sha256: str,
    relative_path: str,
    base_version: Optional[int],
) -> None:
    repository = repository_ctx.entity
    assert repository is not None
    repository_href = repository["pulp_href"]

    base_version_href: Optional[str]
    if base_version is not None:
        base_version_href = f"{repository_href}versions/{base_version}/"
    else:
        base_version_href = None

    content_href = PulpFileContentContext(pulp_ctx).find(
        sha256=sha256, relative_path=relative_path
    )["pulp_href"]

    repository_ctx.modify(
        href=repository_href,
        remove_content=[content_href],
        base_version=base_version_href,
    )
