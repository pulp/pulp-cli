import gettext
from typing import Any, Dict

import click

from pulpcore.cli.common.context import (
    EntityFieldDefinition,
    PulpContext,
    PulpEntityContext,
    PulpRepositoryContext,
    pass_pulp_context,
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
    repository_href_option,
    repository_option,
    resource_option,
    retained_versions_option,
    show_command,
    update_command,
    version_command,
)
from pulpcore.cli.container.context import (
    PulpContainerPushRepositoryContext,
    PulpContainerRemoteContext,
    PulpContainerRepositoryContext,
)
from pulpcore.cli.core.generic import task_command

_ = gettext.gettext


remote_option = resource_option(
    "--remote",
    default_plugin="container",
    default_type="container",
    context_table={"container:container": PulpContainerRemoteContext},
)


@click.group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["container", "push"], case_sensitive=False),
    default="container",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpContext, repo_type: str) -> None:
    if repo_type == "container":
        ctx.obj = PulpContainerRepositoryContext(pulp_ctx)
    elif repo_type == "push":
        ctx.obj = PulpContainerPushRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option]
nested_lookup_options = [repository_href_option, repository_option]
update_options = [
    click.option("--description"),
    remote_option,
    retained_versions_option,
]
create_options = update_options + [click.option("--name", required=True)]

repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(create_command(decorators=create_options))
repository.add_command(update_command(decorators=lookup_options + update_options))
repository.add_command(destroy_command(decorators=lookup_options))
repository.add_command(task_command(decorators=nested_lookup_options))
repository.add_command(version_command(decorators=nested_lookup_options))
repository.add_command(label_command(decorators=nested_lookup_options))


@repository.command()
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
