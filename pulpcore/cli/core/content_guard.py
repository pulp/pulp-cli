import typing as t

import click
from pulp_glue.certguard.context import PulpRHSMCertGuardContext, PulpX509CertGuardContext
from pulp_glue.common.context import PulpContentGuardContext, PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import (
    PulpCompositeContentGuardContext,
    PulpContentRedirectContentGuardContext,
    PulpHeaderContentGuardContext,
    PulpRbacContentGuardContext,
)

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    href_option,
    list_command,
    load_string_callback,
    name_option,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    resource_option,
    role_command,
    show_command,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def content_guard(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpContentGuardContext(pulp_ctx)


common_update_options = [
    click.option("--description"),
]
common_create_options = [
    click.option("--name", required=True),
] + common_update_options
filter_options = [click.option("--name")]
lookup_options = [name_option, href_option]

content_guard.add_command(list_command(decorators=filter_options))


@content_guard.group()
@pass_pulp_context
@click.pass_context
def composite(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpCompositeContentGuardContext(pulp_ctx)


composite_options = [
    resource_option(
        "--guard",
        "guards",
        context_table=PulpContentGuardContext.TYPE_REGISTRY,
        default_plugin="core",
        multiple=True,
    ),
]

composite.add_command(list_command(decorators=filter_options))
composite.add_command(create_command(decorators=common_create_options + composite_options))
composite.add_command(show_command(decorators=lookup_options))
composite.add_command(
    update_command(decorators=lookup_options + common_update_options + composite_options)
)
composite.add_command(destroy_command(decorators=lookup_options))
composite.add_command(role_command(decorators=lookup_options))


@content_guard.group()
@pass_pulp_context
@click.pass_context
def header(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpHeaderContentGuardContext(pulp_ctx)


header_create_options = [
    click.option("--header-name", required=True),
    click.option("--header-value", required=True),
    click.option("--jq-filter"),
]
header_update_options = [
    click.option("--header-name"),
    click.option("--header-value"),
    click.option("--jq-filter"),
]

header.add_command(list_command(decorators=filter_options))
header.add_command(create_command(decorators=common_create_options + header_create_options))
header.add_command(show_command(decorators=lookup_options))
header.add_command(
    update_command(decorators=lookup_options + common_update_options + header_update_options)
)
header.add_command(destroy_command(decorators=lookup_options))
header.add_command(role_command(decorators=lookup_options))


@content_guard.group()
@pass_pulp_context
@click.pass_context
def rbac(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpRbacContentGuardContext(pulp_ctx)


rbac.add_command(list_command(decorators=filter_options))
rbac.add_command(create_command(decorators=common_create_options))
rbac.add_command(show_command(decorators=lookup_options))
rbac.add_command(update_command(decorators=lookup_options + common_update_options))
rbac.add_command(destroy_command(decorators=lookup_options))
rbac.add_command(role_command(decorators=lookup_options))


@rbac.command()
@name_option
@href_option
@click.option(
    "--group",
    "groups",
    help=_("Group to add download role to. Can be specified multiple times."),
    multiple=True,
)
@click.option(
    "--user",
    "users",
    help=_("User to add download role to. Can be specified multiple times."),
    multiple=True,
)
@pass_entity_context
@pass_pulp_context
def assign(
    pulp_ctx: PulpCLIContext,
    guard_ctx: PulpEntityContext,
    users: t.Optional[t.List[str]],
    groups: t.Optional[t.List[str]],
) -> None:
    assert isinstance(guard_ctx, PulpRbacContentGuardContext)

    result = guard_ctx.assign(users=users, groups=groups)
    pulp_ctx.output_result(result)


@rbac.command()
@name_option
@href_option
@click.option(
    "--group",
    "groups",
    help=_("Group to remove download role from. Can be specified multiple times."),
    multiple=True,
)
@click.option(
    "--user",
    "users",
    help=_("User to remove download role from. Can be specified multiple times."),
    multiple=True,
)
@pass_entity_context
@pass_pulp_context
def remove(
    pulp_ctx: PulpCLIContext,
    guard_ctx: PulpEntityContext,
    users: t.Optional[t.List[str]],
    groups: t.Optional[t.List[str]],
) -> None:
    assert isinstance(guard_ctx, PulpRbacContentGuardContext)

    result = guard_ctx.remove(users=users, groups=groups)
    pulp_ctx.output_result(result)


@content_guard.group()
@pass_pulp_context
@click.pass_context
def redirect(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpContentRedirectContentGuardContext(pulp_ctx)


redirect.add_command(list_command(decorators=filter_options))
redirect.add_command(create_command(decorators=common_create_options))
redirect.add_command(show_command(decorators=lookup_options))
redirect.add_command(update_command(decorators=lookup_options + common_update_options))
redirect.add_command(destroy_command(decorators=lookup_options))
redirect.add_command(role_command(decorators=lookup_options))


@content_guard.group()
@pass_pulp_context
@click.pass_context
def x509(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpX509CertGuardContext(pulp_ctx)


certguard_create_options = common_create_options + [
    click.option("--description"),
    click.option(
        "--ca-certificate",
        help=_("a PEM encoded CA certificate or @file containing same"),
        callback=load_string_callback,
        required=True,
    ),
]

certguard_update_options = lookup_options + [
    click.option("--description"),
    click.option(
        "--ca-certificate",
        help=_("a PEM encoded CA certificate or @file containing same"),
        callback=load_string_callback,
    ),
]


x509.add_command(list_command(decorators=filter_options))
x509.add_command(create_command(decorators=certguard_create_options))
x509.add_command(show_command(decorators=lookup_options))
x509.add_command(update_command(decorators=certguard_update_options))
x509.add_command(destroy_command(decorators=lookup_options))


@content_guard.group()
@pass_pulp_context
@click.pass_context
def rhsm(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpRHSMCertGuardContext(pulp_ctx)


rhsm.add_command(list_command(decorators=filter_options))
rhsm.add_command(create_command(decorators=certguard_create_options))
rhsm.add_command(show_command(decorators=lookup_options))
rhsm.add_command(update_command(decorators=certguard_update_options))
rhsm.add_command(destroy_command(decorators=lookup_options))
