import typing as t

import click

from pulp_glue.common.i18n import get_translation

from pulp_cli.generic import pulp_group
from pulpcore.cli.rust.content import content
from pulpcore.cli.rust.distribution import distribution
from pulpcore.cli.rust.remote import remote
from pulpcore.cli.rust.repository import repository

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group(name="rust")
def rust_group() -> None:
    pass


def mount(main: click.Group, **kwargs: t.Any) -> None:
    rust_group.add_command(repository)
    rust_group.add_command(remote)
    rust_group.add_command(distribution)
    rust_group.add_command(content)
    main.add_command(rust_group)
