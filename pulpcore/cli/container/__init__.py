import gettext

from pulpcore.cli.common import main
from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.container.distribution import distribution
from pulpcore.cli.container.namespace import namespace
from pulpcore.cli.container.remote import remote
from pulpcore.cli.container.repository import repository

_ = gettext.gettext


@main.group()
@pass_pulp_context
def container(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin("container")


container.add_command(repository)
container.add_command(remote)
container.add_command(namespace)
container.add_command(distribution)
