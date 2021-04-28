import gettext
from typing import Any, Dict, List, Optional, Union

import click

from pulpcore.cli.common.context import (
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
    PulpRepositoryContext,
    pass_pulp_context,
    pass_repository_context,
)
from pulpcore.cli.common.generic import (
    GroupOption,
    create_command,
    create_content_json_callback,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    load_json_callback,
    name_option,
    pulp_option,
    repository_content_command,
    repository_href_option,
    repository_option,
    show_command,
    update_command,
    version_command,
)
from pulpcore.cli.core.generic import task_command
from pulpcore.cli.file.context import (
    PulpFileContentContext,
    PulpFileRemoteContext,
    PulpFileRepositoryContext,
)

_ = gettext.gettext


def _remote_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[Union[str, PulpEntityContext]]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx: PulpContext = ctx.find_object(PulpContext)
        return PulpFileRemoteContext(pulp_ctx, entity={"name": value})
    return value


def _content_callback(ctx: click.Context, param: click.Parameter, value: Any) -> Optional[str]:
    if value:
        pulp_ctx: PulpContext = ctx.find_object(PulpContext)
        ctx.obj = PulpFileContentContext(pulp_ctx, entity=value)
    return str(value)


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
nested_lookup_options = [repository_href_option, repository_option]
update_options = [
    click.option("--description"),
    click.option("--remote", callback=_remote_callback),
    click.option("--manifest"),
    pulp_option(
        "--autopublish/--no-autopublish",
        needs_plugins=[PluginRequirement("file", "1.7.0")],
        default=None,
    ),
    pulp_option("--retained-versions", needs_plugins=[PluginRequirement("core", "3.13.0.dev")]),
]
create_options = update_options + [
    click.option("--name", required=True),
]
file_options = [
    click.option("--sha256", cls=GroupOption, expose_value=False, group=["relative_path"]),
    click.option(
        "--relative-path",
        cls=GroupOption,
        expose_value=False,
        group=["sha256"],
        callback=_content_callback,
    ),
]
content_json_callback = create_content_json_callback(PulpFileContentContext)
modify_options = [
    click.option(
        "--add-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to add to the repository.
    Each object should consist of the following keys: "sha256", "relative_path"..
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
    click.option(
        "--remove-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to remove from the repository.
    Each object should consist of the following keys: "sha256", "relative_path"..
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
]

repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(create_command(decorators=create_options))
repository.add_command(update_command(decorators=lookup_options + update_options))
repository.add_command(destroy_command(decorators=lookup_options))
repository.add_command(task_command(decorators=nested_lookup_options))
repository.add_command(version_command(decorators=nested_lookup_options))
repository.add_command(label_command(decorators=nested_lookup_options))
repository.add_command(
    repository_content_command(
        contexts={"file": PulpFileContentContext},
        add_decorators=file_options,
        remove_decorators=file_options,
        modify_decorators=modify_options,
    )
)


@repository.command()
@name_option
@href_option
@click.option("--remote", callback=_remote_callback)
@pass_repository_context
def sync(
    repository_ctx: PulpRepositoryContext,
    remote: Optional[Union[str, PulpEntityContext]],
) -> None:
    repository = repository_ctx.entity
    repository_href = repository_ctx.pulp_href

    body = {}

    if isinstance(remote, PulpEntityContext):
        body["remote"] = remote.pulp_href
    elif repository["remote"] is None:
        name = repository["name"]
        raise click.ClickException(
            f"Repository '{name}' does not have a default remote. Please specify with '--remote'."
        )

    repository_ctx.sync(
        href=repository_href,
        body=body,
    )


@repository.command(deprecated=True)
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
    """Please use 'content add' instead."""
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


@repository.command(deprecated=True)
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
    """Please use 'content remove' instead."""
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


@repository.command(deprecated=True)
@name_option
@href_option
@click.option("--base-version", type=int)
@click.option(
    "--add-content",
    default="[]",
    callback=load_json_callback,
    expose_value=True,
    help=_(
        """JSON string with a list of objects to add to the repository.
    Each object should consist of the following keys: "sha256", "relative_path"..
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
    ),
)
@click.option(
    "--remove-content",
    default="[]",
    callback=load_json_callback,
    expose_value=True,
    help=_(
        """JSON string with a list of objects to remove from the repository.
    Each object should consist of the following keys: "sha256", "relative_path"..
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
    ),
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
    """Please use 'content modify' instead."""
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
