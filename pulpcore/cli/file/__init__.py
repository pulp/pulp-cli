from typing import Any

import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import pulp_group
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.file.acs import acs
from pulpcore.cli.file.content import content
from pulpcore.cli.file.distribution import distribution
from pulpcore.cli.file.publication import publication
from pulpcore.cli.file.remote import remote
from pulpcore.cli.file.repository import repository

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group(name="file")
@pass_pulp_context
def file_group(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("file", min="1.6.0"))


def mount(main: click.Group, **kwargs: Any) -> None:
    file_group.add_command(repository)
    file_group.add_command(remote)
    file_group.add_command(publication)
    file_group.add_command(distribution)
    file_group.add_command(content)
    file_group.add_command(acs)
    main.add_command(file_group)
