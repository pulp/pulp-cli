import typing as t

import click
from pulp_glue.common.context import PluginRequirement, PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpDomainContext, PulpUserContext, PulpUserRoleContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    href_option,
    list_command,
    lookup_callback,
    null_callback,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    pulp_option,
    resource_option,
    show_command,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


def _object_required_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    # Ensure --object is specified with "" when --domain is not being used
    if value is None:
        if ctx.get_parameter_source("domain") is None:
            raise click.ClickException(
                _('--object must be set when not using --domain. Use "" to specify a global role.')
            )
        value = ""
    return value


def _object_required_userrole_lookup_callback(
    ctx: click.Context, param: click.Parameter, value: str
) -> t.Optional[str]:
    value = _object_required_callback(ctx, param, value)
    userrole_lookup_callback = lookup_callback("content_object", PulpUserRoleContext)
    return userrole_lookup_callback(ctx, param, value)


req_core_3_17 = PluginRequirement("core", specifier=">=3.17.0")

username_option = pulp_option(
    "--username",
    help=_("Username of the {entity}"),
    expose_value=False,
    callback=lookup_callback("username", PulpUserContext),
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
domain_user_lookup_option = resource_option(
    "--domain",
    parent_resource_lookup=("domain", PulpUserRoleContext),
    expose_value=False,
    **domain_field_options,
)
lookup_options = [
    href_option,
    username_option,
]
update_options = [
    click.option(
        "--password",
        help=_(
            "Password for the user. Provide an empty string to disable password authentication."
        ),
    ),
    click.option("--first-name"),
    click.option("--last-name"),
    click.option("--email"),
    click.option("--staff/--no-staff", "is_staff", default=None),
    click.option("--active/--inactive", "is_active", default=None),
]
create_options = update_options + [
    click.option("--username", required=True),
]


@pulp_group()
@pass_pulp_context
@click.pass_context
def user(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpUserContext(pulp_ctx)


user.add_command(list_command())
user.add_command(show_command(decorators=lookup_options))
user.add_command(create_command(decorators=create_options, needs_plugins=[req_core_3_17]))
user.add_command(
    update_command(decorators=lookup_options + update_options, needs_plugins=[req_core_3_17])
)
user.add_command(destroy_command(decorators=lookup_options, needs_plugins=[req_core_3_17]))


@user.group(name="role-assignment")
@pass_entity_context
@pass_pulp_context
@click.pass_context
def role(ctx: click.Context, pulp_ctx: PulpCLIContext, user_ctx: PulpEntityContext) -> None:
    assert isinstance(user_ctx, PulpUserContext)

    pulp_ctx.needs_plugin(req_core_3_17)
    ctx.obj = PulpUserRoleContext(pulp_ctx, user_ctx)


role.add_command(
    list_command(
        decorators=[
            username_option,
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
            username_option,
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
            username_option,
            click.option(
                "--role",
                required=True,
                callback=lookup_callback("role", PulpUserRoleContext),
                expose_value=False,
            ),
            click.option(
                "--object",
                "content_object",
                callback=_object_required_userrole_lookup_callback,
                expose_value=False,
                help=_('Associated object; use "" for global assignments.'),
            ),
            domain_user_lookup_option,
        ]
    ),
    name="remove",
)
