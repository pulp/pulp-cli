from typing import Any

import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import pulp_group
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.rpm.acs import acs
from pulpcore.cli.rpm.comps import comps_upload
from pulpcore.cli.rpm.content import content
from pulpcore.cli.rpm.distribution import distribution
from pulpcore.cli.rpm.publication import publication
from pulpcore.cli.rpm.remote import remote
from pulpcore.cli.rpm.repository import repository

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
def rpm(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("rpm", min="3.9"))


def mount(main: click.Group, **kwargs: Any) -> None:
    rpm.add_command(repository)
    rpm.add_command(remote)
    rpm.add_command(publication)
    rpm.add_command(distribution)
    rpm.add_command(content)
    rpm.add_command(acs)
    rpm.add_command(comps_upload)
    main.add_command(rpm)
