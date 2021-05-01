import gettext

from pulpcore.cli.common import main
from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.file.content import content
from pulpcore.cli.file.distribution import distribution
from pulpcore.cli.file.publication import publication
from pulpcore.cli.file.remote import remote
from pulpcore.cli.file.repository import repository

_ = gettext.gettext


@main.group(name="file")
@pass_pulp_context
def file_group(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("file"))


file_group.add_command(repository)
file_group.add_command(remote)
file_group.add_command(publication)
file_group.add_command(distribution)
file_group.add_command(content)
