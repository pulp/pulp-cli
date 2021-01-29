import click

from pulpcore.cli.common.context import PulpContext, PulpEntityContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    href_option,
    list_command,
    load_json_callback,
    show_command,
    update_command,
)
from pulpcore.cli.core.context import PulpAccessPolicyContext


def _vs_name_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx: PulpEntityContext = ctx.find_object(PulpEntityContext)
        entity_ctx.entity = {"viewset_name": value}
    return value


@click.group()
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
    click.option("--permissions-assignment", callback=load_json_callback),
]

access_policy.add_command(list_command())
access_policy.add_command(show_command(decorators=lookup_options))
access_policy.add_command(update_command(decorators=lookup_options + update_options))
