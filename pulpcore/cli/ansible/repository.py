from typing import Any

import click
import schema as s

from pulpcore.cli.ansible.context import (
    PulpAnsibleCollectionRemoteContext,
    PulpAnsibleCollectionVersionContext,
    PulpAnsibleRepositoryContext,
    PulpAnsibleRoleContext,
    PulpAnsibleRoleRemoteContext,
)
from pulpcore.cli.common.context import (
    EntityFieldDefinition,
    PulpContext,
    PulpEntityContext,
    PulpRemoteContext,
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
    name_option,
    repository_content_command,
    resource_option,
    retained_versions_option,
    show_command,
    type_option,
    update_command,
    version_command,
)
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


remote_option = resource_option(
    "--remote",
    default_plugin="ansible",
    default_type="collection",
    context_table={
        "ansible:collection": PulpAnsibleCollectionRemoteContext,
        "ansible:role": PulpAnsibleRoleRemoteContext,
    },
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_(
        "Remote used for synching in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
    ),
)


CONTENT_LIST_SCHEMA = s.Schema(
    [{"name": s.And(str, len), "namespace": s.And(str, len), "version": s.And(str, len)}]
)


def _content_callback(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    if value:
        ctx.obj.entity = value  # The context is set by the type parameter on the content commands
    return value


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


lookup_options = [href_option, name_option]
create_options = [
    click.option("--name", required=True),
    click.option("--description"),
    remote_option,
    retained_versions_option,
]
update_options = [
    click.option("--description"),
    remote_option,
    retained_versions_option,
]
content_options = [
    click.option(
        "--name",
        help=_("Name of {entity}"),
        group=["namespace", "version"],
        expose_value=False,
        cls=GroupOption,
        callback=_content_callback,
    ),
    click.option(
        "--namespace",
        help=_("Namespace of {entity}"),
        group=["name", "version"],
        expose_value=False,
        cls=GroupOption,
    ),
    click.option(
        "--version",
        help=_("Version of {entity}"),
        group=["namespace", "name"],
        expose_value=False,
        cls=GroupOption,
    ),
    type_option(
        choices={
            "collection-version": PulpAnsibleCollectionVersionContext,
            "role": PulpAnsibleRoleContext,
        },
        default="collection-version",
    ),
    href_option,
]
content_json_callback = create_content_json_callback(schema=CONTENT_LIST_SCHEMA)
modify_options = [
    click.option(
        "--add-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to add to the repository.
    Each object must contain the following keys: "name", "namespace", "version".
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
    click.option(
        "--remove-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to remove from the repository.
    Each object must contain the following keys: "name", "namespace", "version".
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
    type_option(
        choices={
            "collection-version": PulpAnsibleCollectionVersionContext,
            "role": PulpAnsibleRoleContext,
        },
        default="collection-version",
    ),
]


repository.add_command(show_command(decorators=lookup_options))
repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(destroy_command(decorators=lookup_options))
repository.add_command(version_command())
repository.add_command(create_command(decorators=create_options))
repository.add_command(update_command(decorators=lookup_options + update_options))
repository.add_command(label_command())
repository.add_command(
    repository_content_command(
        contexts={
            "collection-version": PulpAnsibleCollectionVersionContext,
            "role": PulpAnsibleRoleContext,
        },
        add_decorators=content_options,
        remove_decorators=content_options,
        modify_decorators=modify_options,
    )
)


@repository.command()
@name_option
@href_option
@remote_option
@pass_repository_context
def sync(
    repository_ctx: PulpRepositoryContext,
    remote: EntityFieldDefinition,
) -> None:
    """
    If remote is not specified sync will try to use the default remote associated with
    the repository
    """
    repository = repository_ctx.entity
    repository_href = repository["pulp_href"]
    body = {}
    if isinstance(remote, PulpEntityContext):
        body["remote"] = remote.pulp_href
    elif repository["remote"] is None:
        name = repository["name"]
        raise click.ClickException(
            _(
                "Repository '{name}' does not have a default remote."
                " Please specify with '--remote'."
            ).format(name=name)
        )

    repository_ctx.sync(
        href=repository_href,
        body=body,
    )
