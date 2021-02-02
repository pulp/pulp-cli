import json
from typing import Any, Dict, List, Optional, Union

import click

from pulpcore.cli.common.context import (
    PulpContext,
    PulpRepositoryContext,
    pass_pulp_context,
    pass_repository_context,
)
from pulpcore.cli.common.generic import (
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    show_command,
    version_command,
)
from pulpcore.cli.file.context import (
    PulpFileContentContext,
    PulpFileRemoteContext,
    PulpFileRepositoryContext,
)


@click.group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpContext, repo_type: str) -> None:
    if repo_type == "file":
        ctx.obj = PulpFileRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option]

repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(destroy_command(decorators=lookup_options))
repository.add_command(version_command())
repository.add_command(label_command())


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
        remote_href: str = PulpFileRemoteContext(pulp_ctx, entity={"name": remote}).pulp_href
        repository["remote"] = remote_href

    result = repository_ctx.create(body=repository)
    pulp_ctx.output_result(result)


@repository.command()
@name_option
@href_option
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
    repository_href = repository_ctx.pulp_href

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
            remote_href: str = PulpFileRemoteContext(pulp_ctx, entity={"name": remote}).pulp_href
            repository["remote"] = remote_href

    repository_ctx.update(repository_href, body=repository)


@repository.command()
@name_option
@href_option
@click.option("--remote")
@pass_repository_context
@pass_pulp_context
def sync(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    remote: Optional[str],
) -> None:
    repository = repository_ctx.entity
    repository_href = repository_ctx.pulp_href

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


@repository.command()
@name_option
@href_option
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
    repository_href = repository_ctx.pulp_href

    base_version_href: Optional[str]
    if base_version is not None:
        base_version_href = f"{repository_href}versions/{base_version}/"
    else:
        base_version_href = None

    content_href = PulpFileContentContext(
        pulp_ctx, entity={"sha256": sha256, "relative_path": relative_path}
    ).pulp_href

    repository_ctx.modify(
        href=repository_href,
        add_content=[content_href],
        base_version=base_version_href,
    )


@repository.command()
@name_option
@href_option
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
    repository_href = repository_ctx.pulp_href

    base_version_href: Optional[str]
    if base_version is not None:
        base_version_href = f"{repository_href}versions/{base_version}/"
    else:
        base_version_href = None

    content_href = PulpFileContentContext(
        pulp_ctx, entity={"sha256": sha256, "relative_path": relative_path}
    ).pulp_href

    repository_ctx.modify(
        href=repository_href,
        remove_content=[content_href],
        base_version=base_version_href,
    )


def _load_json_from_option(
    ctx: click.Context,
    option_name: Any,
    option_value: str,
) -> List[Dict[str, str]]:
    """Load JSON from input string or from file if string starts with @."""
    json_object: List[Dict[str, str]]
    json_string: Union[str, bytes]

    if option_value.startswith("@"):
        json_file = option_value[1:]
        try:
            with click.open_file(json_file, "rb") as fp:
                json_string = fp.read()
        except OSError:
            raise click.ClickException(f"Failed to load content from {json_file}")
    else:
        json_string = option_value

    try:
        json_object = json.loads(json_string)
    except json.decoder.JSONDecodeError:
        raise click.ClickException("Failed to decode JSON")
    else:
        return json_object


@repository.command()
@name_option
@href_option
@click.option("--base-version", type=int)
@click.option(
    "--add-content",
    default="[]",
    callback=_load_json_from_option,
    is_eager=True,
    expose_value=True,
    help="""JSON string with a list of objects to add to the repository.
    Each object should consist of the following keys: "sha256", "relative_path"..
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects.""",
)
@click.option(
    "--remove-content",
    default="[]",
    callback=_load_json_from_option,
    is_eager=True,
    expose_value=True,
    help="""JSON string with a list of objects to remove from the repository.
    Each object should consist of the following keys: "sha256", "relative_path"..
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects.""",
)
@pass_repository_context
@pass_pulp_context
def modify(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    add_content: List[Dict[str, str]],
    remove_content: List[Dict[str, str]],
    base_version: Optional[int],
) -> None:
    repository_href = repository_ctx.pulp_href

    base_version_href: Optional[str]
    if base_version is not None:
        base_version_href = f"{repository_href}versions/{base_version}/"
    else:
        base_version_href = None

    add_content_href = [
        PulpFileContentContext(pulp_ctx, entity=unit).pulp_href for unit in add_content
    ]
    remove_content_href = [
        PulpFileContentContext(pulp_ctx, entity=unit).pulp_href for unit in remove_content
    ]

    repository_ctx.modify(
        href=repository_href,
        add_content=add_content_href,
        remove_content=remove_content_href,
        base_version=base_version_href,
    )
