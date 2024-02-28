import typing as t

import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.file.context import PulpFileACSContext, PulpFileRemoteContext

from pulpcore.cli.common.acs import acs_command
from pulpcore.cli.common.generic import pulp_group
from pulpcore.cli.file.content import content
from pulpcore.cli.file.distribution import distribution
from pulpcore.cli.file.publication import publication
from pulpcore.cli.file.remote import remote
from pulpcore.cli.file.repository import repository

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group(name="file")
def file_group() -> None:
    pass


def mount(main: click.Group, **kwargs: t.Any) -> None:
    file_group.add_command(repository)
    file_group.add_command(remote)
    file_group.add_command(publication)
    file_group.add_command(distribution)
    file_group.add_command(content)
    file_group.add_command(
        acs_command(
            acs_contexts={"file": PulpFileACSContext},
            remote_context_table={"file:file": PulpFileRemoteContext},
        )
    )
    main.add_command(file_group)
