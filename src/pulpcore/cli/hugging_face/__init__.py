import typing as t

import click

from pulp_glue.common.i18n import get_translation

from pulp_cli.generic import pulp_group
from pulpcore.cli.hugging_face.distribution import distribution
from pulpcore.cli.hugging_face.remote import remote
from pulpcore.cli.hugging_face.repository import repository

translation = get_translation(__package__)
_ = translation.gettext

__version__ = "0.1.0"


@pulp_group(name="hugging-face")
def hugging_face() -> None:
    """Manage Hugging Face Hub content via Pulp."""


def mount(main: click.Group, **kwargs: t.Any) -> None:
    hugging_face.add_command(remote)
    hugging_face.add_command(distribution)
    hugging_face.add_command(repository)
    main.add_command(hugging_face)
