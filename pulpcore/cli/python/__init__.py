from pulpcore.cli.common import main
from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.python.content import content
from pulpcore.cli.python.distribution import distribution
from pulpcore.cli.python.publication import publication
from pulpcore.cli.python.remote import remote
from pulpcore.cli.python.repository import repository


@main.group(name="python")
@pass_pulp_context
def python_group(pulp_ctx: PulpContext) -> None:
    pulp_ctx.needs_plugin("python", min_version="3.1.0.dev")


python_group.add_command(repository)
python_group.add_command(remote)
python_group.add_command(publication)
python_group.add_command(distribution)
python_group.add_command(content)
