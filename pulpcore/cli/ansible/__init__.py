from typing import Any

import click

from pulpcore.cli.ansible.content import content
from pulpcore.cli.ansible.distribution import distribution
from pulpcore.cli.ansible.remote import remote
from pulpcore.cli.ansible.repository import repository
from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import pulp_group
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
def ansible(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("ansible", min="0.7"))


def mount(main: click.Group, **kwargs: Any) -> None:
    ansible.add_command(repository)
    ansible.add_command(remote)
    ansible.add_command(distribution)
    ansible.add_command(content)
    main.add_command(ansible)
