import gettext
from typing import List, Optional

import click

from pulpcore.cli.common.context import (
    PluginRequirement,
    PulpContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    list_command,
    name_option,
    show_command,
    update_command,
)
from pulpcore.cli.core.context import PulpContentGuardContext, PulpRbacContentGuardContext

_ = gettext.gettext


@click.group()
@pass_pulp_context
@click.pass_context
def content_guard(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpContentGuardContext(pulp_ctx)


create_options = [click.option("--name", required=True), click.option("--description")]
filter_options = [click.option("--name")]
lookup_options = [name_option, href_option]

content_guard.add_command(list_command(decorators=filter_options))


@content_guard.group()
@pass_pulp_context
@click.pass_context
def rbac(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("core", "3.15.0.dev"))
    ctx.obj = PulpRbacContentGuardContext(pulp_ctx)


rbac.add_command(list_command(decorators=filter_options))
rbac.add_command(create_command(decorators=create_options))
rbac.add_command(show_command(decorators=lookup_options))
rbac.add_command(update_command(decorators=lookup_options))
rbac.add_command(destroy_command(decorators=lookup_options))


@rbac.command()
@name_option
@href_option
@click.option(
    "--group",
    "groups",
    help=_("Group to remove download permission from. Can be specified multiple times."),
    multiple=True,
)
@click.option(
    "--user",
    "users",
    help=_("User to remove download permission from. Can be specified multiple times."),
    multiple=True,
)
@pass_entity_context
@pass_pulp_context
def assign(
    pulp_ctx: PulpContext,
    guard_ctx: PulpRbacContentGuardContext,
    users: Optional[List[str]],
    groups: Optional[List[str]],
) -> None:
    href = guard_ctx.entity["pulp_href"]
    result = guard_ctx.assign(href=href, users=users, groups=groups)
    pulp_ctx.output_result(result)


@rbac.command()
@name_option
@href_option
@click.option(
    "--group",
    "groups",
    help=_("Group to remove download permission from. Can be specified multiple times."),
    multiple=True,
)
@click.option(
    "--user",
    "users",
    help=_("User to remove download permission from. Can be specified multiple times."),
    multiple=True,
)
@pass_entity_context
@pass_pulp_context
def remove(
    pulp_ctx: PulpContext,
    guard_ctx: PulpRbacContentGuardContext,
    users: Optional[List[str]],
    groups: Optional[List[str]],
) -> None:
    href = guard_ctx.entity["pulp_href"]
    result = guard_ctx.remove(href=href, users=users, groups=groups)
    pulp_ctx.output_result(result)
