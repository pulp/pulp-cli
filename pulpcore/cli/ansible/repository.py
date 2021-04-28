import gettext
from typing import Optional

import click

from pulpcore.cli.ansible.context import (
    PulpAnsibleCollectionRemoteContext,
    PulpAnsibleRepositoryContext,
    PulpAnsibleRoleRemoteContext,
)
from pulpcore.cli.common.context import (
    PluginRequirement,
    PulpContext,
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
    pulp_option,
    show_command,
    update_command,
    version_command,
)

_ = gettext.gettext


def _remote_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx: PulpContext = ctx.find_object(PulpContext)
        try:
            return PulpAnsibleCollectionRemoteContext(pulp_ctx, entity={"name": value}).pulp_href
        except click.ClickException:
            return PulpAnsibleRoleRemoteContext(pulp_ctx, entity={"name": value}).pulp_href
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
    click.option("--remote", callback=_remote_callback, help=_("an optional remote")),
    pulp_option("--retained-versions", needs_plugins=[PluginRequirement("core", "3.13.0.dev")]),
]
update_options = [
    click.option("--description"),
    click.option("--remote", callback=_remote_callback, help=_("new optional remote")),
    pulp_option("--retained-versions", needs_plugins=[PluginRequirement("core", "3.13.0.dev")]),
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
@click.option(
    "--remote", callback=_remote_callback, help=_("optional remote name to perform sync with")
)
@pass_repository_context
def sync(
    repository_ctx: PulpRepositoryContext,
    remote: Optional[str],
) -> None:
    """
    If remote is not specified sync will try to use the default remote associated with
    the repository
    """
    repository = repository_ctx.entity
    repository_href = repository["pulp_href"]
    body = {}
    if remote:
        body["remote"] = remote
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
