from typing import Any, Dict

import click

from pulpcore.cli.common.context import (
    EntityFieldDefinition,
    PulpEntityContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    pass_repository_context,
)
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    pulp_group,
    repository_href_option,
    repository_option,
    resource_option,
    retained_versions_option,
    show_command,
    type_option,
    update_command,
    version_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.container.context import (
    PulpContainerPushRepositoryContext,
    PulpContainerRemoteContext,
    PulpContainerRepositoryContext,
)
from pulpcore.cli.core.generic import task_command

translation = get_translation(__name__)
_ = translation.gettext


remote_option = resource_option(
    "--remote",
    default_plugin="container",
    default_type="container",
    context_table={"container:container": PulpContainerRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_(
        "Remote used for synching in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
    ),
)


@pulp_group()
@type_option(
    choices={
        "container": PulpContainerRepositoryContext,
        "push": PulpContainerPushRepositoryContext,
    },
    default="container",
)
def repository() -> None:
    pass


lookup_options = [href_option, name_option]
nested_lookup_options = [repository_href_option, repository_option]
update_options = [
    click.option("--description"),
    remote_option,
    retained_versions_option,
]
create_options = update_options + [click.option("--name", required=True)]
container_context = (PulpContainerRepositoryContext,)

repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(
    create_command(decorators=create_options, allowed_with_contexts=container_context)
)
repository.add_command(
    update_command(
        decorators=lookup_options + update_options, allowed_with_contexts=container_context
    )
)
repository.add_command(
    destroy_command(decorators=lookup_options, allowed_with_contexts=container_context)
)
repository.add_command(task_command(decorators=nested_lookup_options))
repository.add_command(version_command(decorators=nested_lookup_options))
repository.add_command(label_command(decorators=nested_lookup_options))


@repository.command(allowed_with_contexts=container_context)
@name_option
@href_option
@remote_option
@pass_repository_context
def sync(
    repository_ctx: PulpRepositoryContext,
    remote: EntityFieldDefinition,
) -> None:
    if not repository_ctx.capable("sync"):
        raise click.ClickException(_("Repository type does not support sync."))

    repository = repository_ctx.entity
    repository_href = repository_ctx.pulp_href

    body: Dict[str, Any] = {}

    if isinstance(remote, PulpEntityContext):
        body["remote"] = remote.pulp_href
    elif repository["remote"] is None:
        raise click.ClickException(
            _(
                "Repository '{name}' does not have a default remote. "
                "Please specify with '--remote'."
            ).format(name=repository["name"])
        )

    repository_ctx.sync(
        href=repository_href,
        body=body,
    )
