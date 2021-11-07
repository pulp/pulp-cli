from typing import Any

import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import pulp_group
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.container.content import content
from pulpcore.cli.container.distribution import distribution
from pulpcore.cli.container.namespace import namespace
from pulpcore.cli.container.remote import remote
from pulpcore.cli.container.repository import repository

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
def container(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("container", min="2.3"))


def mount(main: click.Group, **kwargs: Any) -> None:
    container.add_command(repository)
    container.add_command(remote)
    container.add_command(namespace)
    container.add_command(distribution)
    container.add_command(content)
    main.add_command(container)
