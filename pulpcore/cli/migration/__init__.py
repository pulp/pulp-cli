import typing as t

import click
from pulp_glue.common.context import PluginRequirement

from pulpcore.cli.common.generic import PulpCLIContext, pass_pulp_context, pulp_group
from pulpcore.cli.migration.plan import plan
from pulpcore.cli.migration.pulp2 import pulp2


@pulp_group()
@pass_pulp_context
def migration(pulp_ctx: PulpCLIContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("pulp_2to3_migration"))


def mount(main: click.Group, **kwargs: t.Any) -> None:
    migration.add_command(plan)
    migration.add_command(pulp2)
    main.add_command(migration)
