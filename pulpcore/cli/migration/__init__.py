from pulpcore.cli.common import main
from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.migration.plan import plan
from pulpcore.cli.migration.pulp2 import pulp2


@main.group()
@pass_pulp_context
def migration(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin("pulp_2to3_migration")


migration.add_command(plan)
migration.add_command(pulp2)
