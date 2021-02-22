import gettext

from pulpcore.cli.ansible.distribution import distribution
from pulpcore.cli.ansible.remote import remote
from pulpcore.cli.ansible.repository import repository
from pulpcore.cli.common import main
from pulpcore.cli.common.context import PulpContext, pass_pulp_context

_ = gettext.gettext


@main.group()
@pass_pulp_context
def ansible(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin("ansible")


ansible.add_command(repository)
ansible.add_command(remote)
ansible.add_command(distribution)
# TODO add content commands
