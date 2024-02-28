import typing as t

import click
from pulp_glue.common.context import PluginRequirement

from pulpcore.cli.common.generic import PulpCLIContext, pass_pulp_context, pulp_group
from pulpcore.cli.python.content import content
from pulpcore.cli.python.distribution import distribution
from pulpcore.cli.python.publication import publication
from pulpcore.cli.python.remote import remote
from pulpcore.cli.python.repository import repository


@pulp_group(name="python")
@pass_pulp_context
def python_group(pulp_ctx: PulpCLIContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("python", specifier=">=3.1.0"))


def mount(main: click.Group, **kwargs: t.Any) -> None:
    python_group.add_command(repository)
    python_group.add_command(remote)
    python_group.add_command(publication)
    python_group.add_command(distribution)
    python_group.add_command(content)
    main.add_command(python_group)
