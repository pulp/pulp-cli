import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_entity_context, pass_pulp_context
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    list_command,
    load_json_callback,
    show_command,
)
from pulpcore.cli.migration.context import PulpMigrationPlanContext

_ = gettext.gettext


@click.group()
@pass_pulp_context
@click.pass_context
def plan(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpMigrationPlanContext(pulp_ctx)


plan.add_command(list_command())
plan.add_command(show_command(decorators=[href_option]))
plan.add_command(destroy_command(decorators=[href_option]))

create_options = [
    click.option(
        "--plan",
        required=True,
        callback=load_json_callback,
        help=_(
            "Migration plan in json format. The argument can be prefixed with @ to use a file "
            "containing the json."
        ),
    )
]
plan.add_command(create_command(decorators=create_options))


@plan.command(help="Run migration plan")
@click.option("--href", required=True, help="HREF of the plan")
@pass_entity_context
def run(plan_ctx: PulpMigrationPlanContext, href: str) -> None:
    plan_ctx.run(href)


@plan.command(help="Reset Pulp 3 data for plugins specified in the migration plan")
@click.option("--href", required=True, help="HREF of the plan")
@pass_entity_context
def reset(plan_ctx: PulpMigrationPlanContext, href: str) -> None:
    plan_ctx.reset(href)
