import gettext

import click

from pulpcore.cli.ansible.context import (
    PulpAnsibleCollectionRemoteContext,
    PulpAnsibleRepositoryContext,
    PulpAnsibleRoleRemoteContext,
)
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
    resource_option,
    retained_versions_option,
    show_command,
    update_command,
    version_command,
)

_ = gettext.gettext


remote_option = resource_option(
    "--remote",
    default_plugin="ansible",
    default_type="collection",
    context_table={
        "ansible:collection": PulpAnsibleCollectionRemoteContext,
        "ansible:role": PulpAnsibleRoleRemoteContext,
    },
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

repository.add_command(show_command(decorators=lookup_options))
repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(destroy_command(decorators=lookup_options))
repository.add_command(version_command())
repository.add_command(create_command(decorators=create_options))
repository.add_command(update_command(decorators=lookup_options + update_options))
repository.add_command(label_command())


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
            f"Repository '{name}' does not have a default remote. Please specify with '--remote'."
        )

    repository_ctx.sync(
        href=repository_href,
        body=body,
    )


# TODO Finish 'add' and 'remove' commands when role and collection contexts are implemented
