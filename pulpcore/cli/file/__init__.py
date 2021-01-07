import click

from pulpcore.cli.common import main
from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import version_group
from pulpcore.cli.file.content import content
from pulpcore.cli.file.distribution import distribution
from pulpcore.cli.file.publication import publication
from pulpcore.cli.file.remote import remote
from pulpcore.cli.file.repository import repository


@main.group()
@pass_pulp_context
def file(pulp_ctx: PulpContext) -> None:
    if not pulp_ctx.has_plugin("pulp_file"):
        raise click.ClickException("'pulp_file' does not seem to be installed.")


file.add_command(repository)
repository.add_command(version_group)
file.add_command(remote)
file.add_command(publication)
file.add_command(distribution)
file.add_command(content)
