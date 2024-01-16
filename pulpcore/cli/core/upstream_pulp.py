import click
from pulp_glue.common.context import PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpUpstreamPulpContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    list_command,
    load_string_callback,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    resource_lookup_option,
    show_command,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext

lookup_option = resource_lookup_option(
    "--upstream-pulp", "--id", context_class=PulpUpstreamPulpContext
)
lookup_options = [lookup_option]
update_options = [
    click.option("--base-url"),
    click.option("--api-root"),
    click.option("--domain"),
    click.option("--tls-validation/--no-tls-validation"),
    click.option(
        "--username",
        help=_("The username to authenticate to the upstream pulp."),
    ),
    click.option(
        "--password",
        help=_("The password to authenticate to the upstream pulp."),
    ),
    click.option(
        "--ca-cert",
        help=_("a PEM encoded CA certificate or @file containing same"),
        callback=load_string_callback,
    ),
    click.option(
        "--client-cert",
        help=_("a PEM encoded client certificate or @file containing same"),
        callback=load_string_callback,
    ),
    click.option(
        "--client-key",
        help=_("a PEM encode private key or @file containing same"),
        callback=load_string_callback,
    ),
    click.option("--pulp-label-select"),
]
create_options = [
    click.option("--name", required=True, help=_("Name of the upstream pulp")),
] + update_options


@pulp_group()
@pass_pulp_context
@click.pass_context
def upstream_pulp(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpUpstreamPulpContext(pulp_ctx)


upstream_pulp.add_command(list_command())
upstream_pulp.add_command(show_command(decorators=lookup_options))
upstream_pulp.add_command(create_command(decorators=create_options))
upstream_pulp.add_command(update_command(decorators=lookup_options + update_options))
upstream_pulp.add_command(destroy_command(decorators=lookup_options))


@upstream_pulp.command()
@lookup_option
@pass_entity_context
def replicate(upstream_pulp_ctx: PulpEntityContext) -> None:
    assert isinstance(upstream_pulp_ctx, PulpUpstreamPulpContext)
    upstream_pulp_ctx.replicate()
