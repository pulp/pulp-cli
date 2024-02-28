import typing as t

import click
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.ansible.content import content
from pulpcore.cli.ansible.distribution import distribution
from pulpcore.cli.ansible.remote import remote
from pulpcore.cli.ansible.repository import repository
from pulpcore.cli.common.generic import pulp_group

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
def ansible() -> None:
    pass


def mount(main: click.Group, **kwargs: t.Any) -> None:
    ansible.add_command(repository)
    ansible.add_command(remote)
    ansible.add_command(distribution)
    ansible.add_command(content)
    main.add_command(ansible)
