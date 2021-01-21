from pulpcore.cli.common import main
from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import version_group
from pulpcore.cli.container.repository import repository
from pulpcore.cli.container.remote import remote
from pulpcore.cli.container.distribution import distribution


@main.group()
@pass_pulp_context
def container(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin("pulp_container")


container.add_command(repository)
repository.add_command(version_group)
container.add_command(remote)
container.add_command(distribution)
