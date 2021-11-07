from typing import Any

import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import pulp_group
from pulpcore.cli.migration.plan import plan
from pulpcore.cli.migration.pulp2 import pulp2


@pulp_group()
@pass_pulp_context
def migration(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("pulp_2to3_migration"))


def mount(main: click.Group, **kwargs: Any) -> None:
    migration.add_command(plan)
    migration.add_command(pulp2)
    main.add_command(migration)
