import click
from pulp_glue.common.context import PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpAccessPolicyContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    href_option,
    list_command,
    load_json_callback,
    lookup_callback,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    show_command,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def access_policy(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpAccessPolicyContext(pulp_ctx)


lookup_options = [
    href_option,
    click.option("--viewset-name", callback=lookup_callback("viewset_name"), expose_value=False),
]

update_options = [
    click.option("--statements", callback=load_json_callback),
    click.option("--creation-hooks", callback=load_json_callback),
]

access_policy.add_command(list_command())
access_policy.add_command(show_command(decorators=lookup_options))
access_policy.add_command(update_command(decorators=lookup_options + update_options))


@access_policy.command()
@href_option
@click.option("--viewset-name", callback=lookup_callback("viewset_name"), expose_value=False)
@pass_entity_context
@pass_pulp_context
def reset(pulp_ctx: PulpCLIContext, access_policy_ctx: PulpEntityContext) -> None:
    assert isinstance(access_policy_ctx, PulpAccessPolicyContext)

    result = access_policy_ctx.reset()
    pulp_ctx.output_result(result)
