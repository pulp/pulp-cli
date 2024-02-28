import gettext
import typing as t

import click
from pulp_glue.core.context import PulpRoleContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    href_option,
    list_command,
    name_filter_options,
    name_option,
    pass_pulp_context,
    pulp_group,
    show_command,
    update_command,
)

_ = gettext.gettext
NO_PERMISSION_KEY = "pulpcore.cli.core.role.no_permission"


def _no_permission_callback(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
    ctx.meta[NO_PERMISSION_KEY] = value
    return value


def _permission_callback(
    ctx: click.Context, param: click.Parameter, value: t.Iterable[str]
) -> t.Optional[t.Iterable[str]]:
    if ctx.meta.get(NO_PERMISSION_KEY, False):
        if value:
            raise click.ClickException(_("Cannot specify `--permission` and `--no-permission`."))
        return []
    return value or None


filters = name_filter_options + [
    click.option("--locked/--unlocked", default=None),
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


@pulp_group()
@pass_pulp_context
@click.pass_context
def role(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpRoleContext(pulp_ctx)


role.add_command(list_command(decorators=filters))
role.add_command(show_command(decorators=lookup_options))
role.add_command(create_command(decorators=create_options))
role.add_command(update_command(decorators=lookup_options + update_options))
role.add_command(destroy_command(decorators=lookup_options))
