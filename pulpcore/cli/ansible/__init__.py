from pulpcore.cli.common import main
from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import version_group
from pulpcore.cli.ansible.distribution import distribution
from pulpcore.cli.ansible.remote import remote
from pulpcore.cli.ansible.repository import repository


@main.group()
@pass_pulp_context
def ansible(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin("pulp_ansible")


ansible.add_command(repository)
repository.add_command(version_group)
ansible.add_command(remote)
ansible.add_command(distribution)
# TODO add content commands
