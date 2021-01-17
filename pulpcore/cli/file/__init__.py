import click

from pulpcore.cli.common import main
from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.file.content import content
from pulpcore.cli.file.distribution import distribution
from pulpcore.cli.file.publication import publication
from pulpcore.cli.file.remote import remote
from pulpcore.cli.file.repository import repository


@main.group(name="file")
@pass_pulp_context
def file_group(pulp_ctx: PulpContext) -> None:
    if not pulp_ctx.has_plugin("pulp_file"):
        raise click.ClickException("'pulp_file' does not seem to be installed.")


file_group.add_command(repository)
file_group.add_command(remote)
file_group.add_command(publication)
file_group.add_command(distribution)
file_group.add_command(content)
