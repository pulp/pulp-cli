import click

from pulpcore.cli.common.context import (
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import (
    href_option,
    list_command,
    load_json_callback,
    pulp_group,
    show_command,
    update_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import PulpAccessPolicyContext

translation = get_translation(__name__)
_ = translation.gettext


def _vs_name_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.entity = {"viewset_name": value}
    return value


@pulp_group()
@pass_pulp_context
@click.pass_context
def access_policy(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpAccessPolicyContext(pulp_ctx)


lookup_options = [
    href_option,
    click.option("--viewset-name", callback=_vs_name_callback, expose_value=False),
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
@click.option("--viewset-name", callback=_vs_name_callback, expose_value=False)
@pass_entity_context
@pass_pulp_context
def reset(pulp_ctx: PulpContext, access_policy_ctx: PulpAccessPolicyContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("core", min="3.17"))
    result = access_policy_ctx.reset()
    pulp_ctx.output_result(result)
