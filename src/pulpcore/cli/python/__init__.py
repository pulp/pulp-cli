import typing as t

import click

from pulp_cli.generic import pulp_group
from pulpcore.cli.python.content import content
from pulpcore.cli.python.distribution import distribution
from pulpcore.cli.python.publication import publication
from pulpcore.cli.python.remote import remote
from pulpcore.cli.python.repository import repository


@pulp_group(name="python")
def python_group() -> None:
    pass


def mount(main: click.Group, **kwargs: t.Any) -> None:
    python_group.add_command(repository)
    python_group.add_command(remote)
    python_group.add_command(publication)
    python_group.add_command(distribution)
    python_group.add_command(content)
    main.add_command(python_group)
