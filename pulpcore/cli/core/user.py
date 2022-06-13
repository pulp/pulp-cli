import click

from pulpcore.cli.common.context import (  # PulpEntityContext,; pass_entity_context,
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
    null_callback,
    pulp_group,
    pulp_option,
    show_command,
    update_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import PulpUserContext, PulpUserRoleContext

translation = get_translation(__name__)
_ = translation.gettext


req_core_3_17 = PluginRequirement("core", min="3.17")

username_option = pulp_option(
    "--username",
    help=_("Username of the {entity}"),
    expose_value=False,
    callback=lookup_callback("username", PulpUserContext),
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
def user(ctx: click.Context, pulp_ctx: PulpContext) -> None:
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
def role(ctx: click.Context, pulp_ctx: PulpContext, user_ctx: PulpUserContext) -> None:
    pulp_ctx.needs_plugin(req_core_3_17)
    ctx.obj = PulpUserRoleContext(pulp_ctx, user_ctx)


role.add_command(
    list_command(
        decorators=[
            username_option,
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
            username_option,
            click.option("--role", required=True),
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
                required=True,
                callback=lookup_callback("content_object", PulpUserRoleContext),
                expose_value=False,
                help=_('Associated object; use "" for global assignments.'),
            ),
        ]
    ),
    name="remove",
)
