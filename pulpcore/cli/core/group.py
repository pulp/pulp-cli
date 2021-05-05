import gettext
from typing import Optional

import click

from pulpcore.cli.common.context import PulpContext, pass_entity_context, pass_pulp_context
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    list_command,
    name_option,
    show_command,
)
from pulpcore.cli.core.context import (
    PulpGroupContext,
    PulpGroupModelPermissionContext,
    PulpGroupObjectPermissionContext,
    PulpGroupPermissionContext,
    PulpGroupUserContext,
    PulpUserContext,
)


def _groupname_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx: PulpGroupContext = ctx.find_object(PulpGroupContext)
        entity_ctx.entity = {"name": value}
    return value


def _permission_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx: PulpGroupPermissionContext = ctx.find_object(PulpGroupPermissionContext)
        entity_ctx.entity = {"permission": value}
    return value


def _object_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    entity_ctx: PulpGroupPermissionContext = ctx.find_object(PulpGroupPermissionContext)
    if value is not None:
        if isinstance(entity_ctx, PulpGroupObjectPermissionContext):
            entity_ctx.entity = {"obj": value}
        else:
            raise click.ClickException(_("This type of Permission does not have an object."))
    elif isinstance(entity_ctx, PulpGroupObjectPermissionContext):
        raise click.ClickException(_("This type of Permission needs an object."))
    return value


groupname_option = click.option("--groupname", callback=_groupname_callback, expose_value=False)

_ = gettext.gettext


@click.group(help=_("Manage user groups and their granted permissions."))
@pass_pulp_context
@click.pass_context
def group(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpGroupContext(pulp_ctx)


lookup_options = [name_option, href_option]
create_options = [click.option("--name", required=True)]

group.add_command(list_command())
group.add_command(show_command(decorators=lookup_options))
group.add_command(destroy_command(decorators=lookup_options))
group.add_command(create_command(decorators=create_options))


@group.group()
@click.option(
    "-t",
    "--type",
    "perm_type",
    type=click.Choice(["model", "object"], case_sensitive=False),
    default="model",
)
@pass_entity_context
@pass_pulp_context
@click.pass_context
def permission(
    ctx: click.Context,
    pulp_ctx: PulpContext,
    group_ctx: PulpGroupContext,
    perm_type: str,
) -> None:
    if perm_type == "model":
        ctx.obj = PulpGroupModelPermissionContext(pulp_ctx, group_ctx)
    elif perm_type == "object":
        ctx.obj = PulpGroupObjectPermissionContext(pulp_ctx, group_ctx)
    else:
        raise NotImplementedError()


permission.add_command(
    list_command(
        help=_("Show a list of the permissioons granted to a group."), decorators=[groupname_option]
    )
)


@permission.command(name="add", help=_("Grant a permission to the group."))
@groupname_option
@click.option("--permission", required=True)
@click.option("--object", "obj", callback=_object_callback)
@pass_entity_context
def add_permission(
    entity_ctx: PulpGroupPermissionContext, permission: str, obj: Optional[str]
) -> None:
    body = {"permission": permission}
    if obj:
        body["obj"] = obj
    entity_ctx.create(body=body)


permission.add_command(
    destroy_command(
        name="remove",
        help=_("Revoke a permission from the group."),
        decorators=[
            groupname_option,
            click.option(
                "--permission", required=True, callback=_permission_callback, expose_value=False
            ),
            click.option("--object", callback=_object_callback, expose_value=False),
        ],
    )
)


@group.group()
@pass_entity_context
@pass_pulp_context
@click.pass_context
def user(ctx: click.Context, pulp_ctx: PulpContext, group_ctx: PulpGroupContext) -> None:
    ctx.obj = PulpGroupUserContext(pulp_ctx, group_ctx)


user.add_command(list_command(decorators=[groupname_option]))


@user.command(name="add")
@groupname_option
@click.option("--username", required=True)
@pass_entity_context
def add_user(entity_ctx: PulpGroupUserContext, username: str) -> None:
    entity_ctx.create(body={"username": username})


@user.command(name="remove")
@groupname_option
@click.option("--username", required=True)
@pass_entity_context
@pass_pulp_context
def remove_user(pulp_ctx: PulpContext, entity_ctx: PulpGroupUserContext, username: str) -> None:
    user_href = PulpUserContext(pulp_ctx).find(username=username)["pulp_href"]
    user_pk = user_href.split("/")[-2]
    group_user_href = f"{entity_ctx.group_ctx.pulp_href}users/{user_pk}/"
    entity_ctx.delete(group_user_href)
