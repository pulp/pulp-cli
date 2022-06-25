from typing import Optional

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
    lookup_callback,
    name_option,
    null_callback,
    pulp_group,
    role_command,
    show_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import (
    PulpGroupContext,
    PulpGroupModelPermissionContext,
    PulpGroupObjectPermissionContext,
    PulpGroupPermissionContext,
    PulpGroupRoleContext,
    PulpGroupUserContext,
    PulpUserContext,
)

translation = get_translation(__name__)
_ = translation.gettext


def _object_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    entity_ctx = ctx.find_object(PulpGroupPermissionContext)
    assert entity_ctx is not None
    if value is not None:
        if isinstance(entity_ctx, PulpGroupObjectPermissionContext):
            entity_ctx.entity = {"obj": value}
        else:
            raise click.ClickException(_("This type of Permission does not have an object."))
    elif isinstance(entity_ctx, PulpGroupObjectPermissionContext):
        raise click.ClickException(_("This type of Permission needs an object."))
    return value


group_option = click.option(
    "--group", callback=lookup_callback("name", PulpGroupContext), expose_value=False
)


@pulp_group(help=_("Manage user groups."))
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
group.add_command(
    role_command(decorators=lookup_options, needs_plugins=[PluginRequirement("core", min="3.17")])
)


@group.group(needs_plugins=[PluginRequirement("core", max="3.20-dev")])
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
        help=_("Show a list of the permissioons granted to a group."), decorators=[group_option]
    )
)


@permission.command(name="add", help=_("Grant a permission to the group."))
@group_option
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
            group_option,
            click.option(
                "--permission",
                required=True,
                callback=lookup_callback("permission", PulpGroupPermissionContext),
                expose_value=False,
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


user.add_command(list_command(decorators=[group_option]))
user.add_command(
    create_command(decorators=[group_option, click.option("--username", required=True)]),
    name="add",
)


@user.command(name="remove")
@group_option
@click.option("--username", required=True)
@pass_entity_context
@pass_pulp_context
def remove_user(pulp_ctx: PulpContext, entity_ctx: PulpGroupUserContext, username: str) -> None:
    user_href = PulpUserContext(pulp_ctx).find(username=username)["pulp_href"]
    user_pk = user_href.split("/")[-2]
    group_user_href = f"{entity_ctx.group_ctx.pulp_href}users/{user_pk}/"
    entity_ctx.delete(group_user_href)


@group.group(name="role-assignment")
@pass_entity_context
@pass_pulp_context
@click.pass_context
def role(ctx: click.Context, pulp_ctx: PulpContext, group_ctx: PulpGroupContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("core", min="3.17"))
    ctx.obj = PulpGroupRoleContext(pulp_ctx, group_ctx)


role.add_command(
    list_command(
        decorators=[
            group_option,
            click.option("--role"),
            click.option("--role-in", "role__in"),
            click.option("--role-contains", "role__contains"),
            click.option("--role-icontains", "role__icontains"),
            click.option("--role-startswith", "role__startswith"),
            click.option(
                "--object",
                "content_object",
                callback=null_callback,
                help=_('Filter roles by the associated object. Use "" to list global assignments.'),
            ),
        ]
    )
)
role.add_command(
    create_command(
        decorators=[
            group_option,
            click.option("--role", required=True),
            click.option("--object", "content_object", required=True),
            click.option(
                "--object",
                "content_object",
                required=True,
                help=_('Associated object; use "" for global assignments.'),
            ),
        ]
    ),
    name="add",
)
role.add_command(
    destroy_command(
        decorators=[
            group_option,
            click.option(
                "--role",
                required=True,
                callback=lookup_callback("role", PulpGroupRoleContext),
                expose_value=False,
            ),
            click.option(
                "--object",
                "content_object",
                required=True,
                callback=lookup_callback("content_object", PulpGroupRoleContext),
                expose_value=False,
                help=_('Associated object; use "" for global assignments.'),
            ),
        ]
    ),
    name="remove",
)
