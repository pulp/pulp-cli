import gettext
from typing import Iterable, Optional

import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    list_command,
    name_option,
    show_command,
    update_command,
)
from pulpcore.cli.core.context import PulpRoleContext

_ = gettext.gettext
NO_PERMISSION_KEY = "pulpcore.cli.core.role.no_permission"


def _no_permission_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    ctx.meta[NO_PERMISSION_KEY] = value
    return value


def _permission_callback(
    ctx: click.Context, param: click.Parameter, value: Iterable[str]
) -> Optional[Iterable[str]]:
    if ctx.meta.get(NO_PERMISSION_KEY, False):
        if value:
            raise click.ClickException(_("Cannot specify `--permission` and `--no-permission`."))
        return []
    return value or None


filters = [
    click.option("--locked/--unlocked", default=None),
    click.option("--name"),
    click.option("--name-in", "name__in"),
    click.option("--name-contains", "name__contains"),
    click.option("--name-icontains", "name__icontains"),
    click.option("--name-startswith", "name__startswith"),
]
lookup_options = [href_option, name_option]
update_options = [
    click.option("--description"),
    click.option(
        "--no-permission",
        is_eager=True,
        is_flag=True,
        expose_value=False,
        callback=_no_permission_callback,
    ),
    click.option(
        "--permission",
        "permissions",
        multiple=True,
        help=_("Permission in the form '<app_label>.<codename>'. Can be used multiple times."),
        callback=_permission_callback,
    ),
]
create_options = [
    click.option("--name", required=True, help=_("Name of the role")),
] + update_options


@click.group()
@pass_pulp_context
@click.pass_context
def role(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("core", min="3.17.dev"))
    ctx.obj = PulpRoleContext(pulp_ctx)


role.add_command(list_command(decorators=filters))
role.add_command(show_command(decorators=lookup_options))
role.add_command(create_command(decorators=create_options))
role.add_command(update_command(decorators=lookup_options + update_options))
role.add_command(destroy_command(decorators=lookup_options))
