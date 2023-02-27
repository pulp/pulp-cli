from typing import Any, Dict, List, Optional

import click
import schema as s
from pulp_glue.common.context import (
    EntityFieldDefinition,
    PluginRequirement,
    PulpRemoteContext,
    PulpRepositoryContext,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.file.context import (
    PulpFileContentContext,
    PulpFileRemoteContext,
    PulpFileRepositoryContext,
)

from pulpcore.cli.common.generic import (
    GroupOption,
    PulpCLIContext,
    create_command,
    create_content_json_callback,
    destroy_command,
    href_option,
    json_callback,
    label_command,
    label_select_option,
    list_command,
    load_file_wrapper,
    name_option,
    pass_pulp_context,
    pass_repository_context,
    pulp_group,
    pulp_labels_option,
    pulp_option,
    repository_content_command,
    repository_href_option,
    repository_lookup_option,
    resource_option,
    retained_versions_option,
    role_command,
    show_command,
    update_command,
    version_command,
)
from pulpcore.cli.core.generic import task_command

translation = get_translation(__name__)
_ = translation.gettext


remote_option = resource_option(
    "--remote",
    default_plugin="file",
    default_type="file",
    context_table={"file:file": PulpFileRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_("Remote used for syncing in the form '[[<plugin>:]<resource_type>:]<name>' or by href."),
)


def _content_callback(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    if value:
        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx is not None
        ctx.obj = PulpFileContentContext(pulp_ctx, entity=value)
    return value


CONTENT_LIST_SCHEMA = s.Schema([{"sha256": str, "relative_path": s.And(str, len)}])


@load_file_wrapper
def _content_list_callback(ctx: click.Context, param: click.Parameter, value: Optional[str]) -> Any:
    if value is None:
        return None

    result = json_callback(ctx, param, value)
    try:
        return CONTENT_LIST_SCHEMA.validate(result)
    except s.SchemaError as e:
        raise click.ClickException(
            _("Validation of '{parameter}' failed: {error}").format(
                parameter=param.name, error=str(e)
            )
        )


@pulp_group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpCLIContext, repo_type: str) -> None:
    if repo_type == "file":
        ctx.obj = PulpFileRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option, repository_lookup_option]
nested_lookup_options = [repository_href_option, repository_lookup_option]
update_options = [
    click.option("--description"),
    remote_option,
    click.option("--manifest"),
    pulp_option(
        "--autopublish/--no-autopublish",
        needs_plugins=[PluginRequirement("file", min="1.7.0")],
        default=None,
    ),
    retained_versions_option,
    pulp_labels_option,
]
create_options = update_options + [click.option("--name", required=True)]
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
content_json_callback = create_content_json_callback(
    PulpFileContentContext, schema=CONTENT_LIST_SCHEMA
)
modify_options = [
    click.option(
        "--add-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to add to the repository.
    Each object must contain the following keys: "sha256", "relative_path".
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
    click.option(
        "--remove-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to remove from the repository.
    Each object must contain the following keys: "sha256", "relative_path".
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
repository.add_command(role_command(decorators=lookup_options))


@repository.command()
@name_option
@href_option
@repository_lookup_option
@remote_option
@pass_repository_context
def sync(
    repository_ctx: PulpRepositoryContext,
    remote: EntityFieldDefinition,
) -> None:
    """
    Sync the repository from a remote source.
    If remote is not specified sync will try to use the default remote associated with
    the repository
    """
    body: Dict[str, Any] = {}
    repository = repository_ctx.entity

    if remote:
        body["remote"] = remote
    elif repository["remote"] is None:
        raise click.ClickException(
            _(
                "Repository '{name}' does not have a default remote. "
                "Please specify with '--remote'."
            ).format(name=repository["name"])
        )

    repository_ctx.sync(body=body)


@repository.command(deprecated=True)
@name_option
@href_option
@repository_lookup_option
@click.option("--sha256", required=True)
@click.option("--relative-path", required=True)
@click.option("--base-version", type=int)
@pass_repository_context
@pass_pulp_context
def add(
    pulp_ctx: PulpCLIContext,
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
        add_content=[content_href],
        base_version=base_version_href,
    )


@repository.command(deprecated=True)
@name_option
@href_option
@repository_lookup_option
@click.option("--sha256", required=True)
@click.option("--relative-path", required=True)
@click.option("--base-version", type=int)
@pass_repository_context
@pass_pulp_context
def remove(
    pulp_ctx: PulpCLIContext,
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
        remove_content=[content_href],
        base_version=base_version_href,
    )


@repository.command(deprecated=True)
@name_option
@href_option
@repository_lookup_option
@click.option("--base-version", type=int)
@click.option(
    "--add-content",
    default="[]",
    callback=_content_list_callback,
    expose_value=True,
    help=_(
        """JSON string with a list of objects to add to the repository.
    Each object must contain the following keys: "sha256", "relative_path".
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
    ),
)
@click.option(
    "--remove-content",
    default="[]",
    callback=_content_list_callback,
    expose_value=True,
    help=_(
        """JSON string with a list of objects to remove from the repository.
    Each object must contain the following keys: "sha256", "relative_path".
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
    ),
)
@pass_repository_context
@pass_pulp_context
def modify(
    pulp_ctx: PulpCLIContext,
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
        add_content=add_content_href,
        remove_content=remove_content_href,
        base_version=base_version_href,
    )
