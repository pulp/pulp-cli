from typing import Any

import click
from pulp_glue.common.context import PluginRequirement
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.ansible.content import content
from pulpcore.cli.ansible.distribution import distribution
from pulpcore.cli.ansible.remote import remote
from pulpcore.cli.ansible.repository import repository
from pulpcore.cli.common.generic import PulpCLIContext, pass_pulp_context, pulp_group

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
def ansible(pulp_ctx: PulpCLIContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("ansible", min="0.7.0"))


def mount(main: click.Group, **kwargs: Any) -> None:
    ansible.add_command(repository)
    ansible.add_command(remote)
    ansible.add_command(distribution)
    ansible.add_command(content)
    main.add_command(ansible)
