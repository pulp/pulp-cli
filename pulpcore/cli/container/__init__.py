import typing as t

import click
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import pulp_group
from pulpcore.cli.container.content import content
from pulpcore.cli.container.distribution import distribution
from pulpcore.cli.container.namespace import namespace
from pulpcore.cli.container.remote import remote
from pulpcore.cli.container.repository import repository

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
def container() -> None:
    pass


def mount(main: click.Group, **kwargs: t.Any) -> None:
    container.add_command(repository)
    container.add_command(remote)
    container.add_command(namespace)
    container.add_command(distribution)
    container.add_command(content)
    main.add_command(container)
