import click
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    href_option,
    list_command,
    load_json_callback,
    pass_pulp_context,
    pulp_group,
    show_command,
)
from pulpcore.cli.migration.context import PulpMigrationPlanContext

translation = get_translation(__package__)
_ = translation.gettext

pass_migration_plan_context = click.make_pass_decorator(PulpMigrationPlanContext)


@pulp_group()
@pass_pulp_context
@click.pass_context
def plan(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
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


@plan.command(help=_("Run migration plan"))
@click.option("--href", required=True, help=_("HREF of the plan"))
@pass_migration_plan_context
def run(plan_ctx: PulpMigrationPlanContext, href: str) -> None:
    plan_ctx.run(href)


@plan.command(help=_("Reset Pulp 3 data for plugins specified in the migration plan"))
@click.option("--href", required=True, help=_("HREF of the plan"))
@pass_migration_plan_context
def reset(plan_ctx: PulpMigrationPlanContext, href: str) -> None:
    plan_ctx.reset(href)
