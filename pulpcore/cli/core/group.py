import typing as t

import click
from pulp_glue.common.context import PluginRequirement, PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import (
    PulpDomainContext,
    PulpGroupContext,
    PulpGroupModelPermissionContext,
    PulpGroupObjectPermissionContext,
    PulpGroupPermissionContext,
    PulpGroupRoleContext,
    PulpGroupUserContext,
    PulpUserContext,
)

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    href_option,
    list_command,
    lookup_callback,
    name_option,
    null_callback,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    resource_option,
    role_command,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext

pass_group_context = click.make_pass_decorator(PulpGroupContext)


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


def _object_required_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    # Ensure --object is specified with "" when --domain is not being used
    if value is None:
        if ctx.get_parameter_source("domain") is None:
            raise click.ClickException(
                _('--object must be set when not using --domain. Use "" to specify a global role.')
            )
        value = ""
    return value


def _object_required_grouprole_lookup_callback(
    ctx: click.Context, param: click.Parameter, value: str
) -> t.Optional[str]:
    value = _object_required_callback(ctx, param, value)
    grouprole_lookup_callback = lookup_callback("content_object", PulpGroupRoleContext)
    return grouprole_lookup_callback(ctx, param, value)


group_option = click.option(
    "--group", callback=lookup_callback("name", PulpGroupContext), expose_value=False
)
domain_field_options = {
    "default_plugin": "core",
    "default_type": "domain",
    "context_table": {
        "core:domain": PulpDomainContext,
    },
    "help": _("Domain the role is applied in"),
    "needs_plugins": (PluginRequirement("core", specifier=">=3.23"),),
}
domain_option = resource_option("--domain", **domain_field_options)
domain_group_lookup_option = resource_option(
    "--domain",
    parent_resource_lookup=("domain", PulpGroupRoleContext),
    expose_value=False,
    **domain_field_options,
)


@pulp_group(help=_("Manage user groups."))
@pass_pulp_context
@click.pass_context
def group(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpGroupContext(pulp_ctx)


lookup_options = [name_option, href_option]
create_options = [click.option("--name", required=True)]

group.add_command(list_command())
group.add_command(show_command(decorators=lookup_options))
group.add_command(destroy_command(decorators=lookup_options))
group.add_command(create_command(decorators=create_options))
group.add_command(
    role_command(
        decorators=lookup_options, needs_plugins=[PluginRequirement("core", specifier=">=3.17.0")]
    )
)


@group.group(needs_plugins=[PluginRequirement("core", specifier="<3.20.0")])
@click.option(
    "-t",
    "--type",
    "perm_type",
    type=click.Choice(["model", "object"], case_sensitive=False),
    default="model",
)
@pass_group_context
@pass_pulp_context
@click.pass_context
def permission(
    ctx: click.Context,
    pulp_ctx: PulpCLIContext,
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
def add_permission(entity_ctx: PulpEntityContext, permission: str, obj: t.Optional[str]) -> None:
    assert isinstance(entity_ctx, PulpGroupPermissionContext)

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
@pass_group_context
@pass_pulp_context
@click.pass_context
def user(ctx: click.Context, pulp_ctx: PulpCLIContext, group_ctx: PulpGroupContext) -> None:
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
def remove_user(pulp_ctx: PulpCLIContext, entity_ctx: PulpEntityContext, username: str) -> None:
    assert isinstance(entity_ctx, PulpGroupUserContext)

    user = PulpUserContext(pulp_ctx, entity={"username": username})
    entity_ctx.group_ctx.remove_user(user)


@group.group(name="role-assignment")
@pass_group_context
@pass_pulp_context
@click.pass_context
def role(ctx: click.Context, pulp_ctx: PulpCLIContext, group_ctx: PulpGroupContext) -> None:
    ctx.obj = PulpGroupRoleContext(pulp_ctx, group_ctx)


role.add_command(
    list_command(
        decorators=[
            group_option,
            click.option("--role"),
            click.option("--role-in", "role__in", multiple=True),
            click.option("--role-contains", "role__contains"),
            click.option("--role-icontains", "role__icontains"),
            click.option("--role-startswith", "role__startswith"),
            click.option(
                "--object",
                "content_object",
                callback=null_callback,
                help=_('Filter roles by the associated object. Use "" to list global assignments.'),
            ),
            domain_option,
        ]
    )
)
role.add_command(
    create_command(
        decorators=[
            group_option,
            click.option("--role", required=True),
            click.option(
                "--object",
                "content_object",
                callback=_object_required_callback,
                help=_('Associated object; use "" for global assignments.'),
            ),
            domain_option,
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
                callback=_object_required_grouprole_lookup_callback,
                expose_value=False,
                help=_('Associated object; use "" for global assignments.'),
            ),
            domain_group_lookup_option,
        ]
    ),
    name="remove",
)
