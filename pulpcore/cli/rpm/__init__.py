import click

from pulpcore.cli.common import main
from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import version_group
from pulpcore.cli.rpm.repository import repository
from pulpcore.cli.rpm.remote import remote
from pulpcore.cli.rpm.publication import publication
from pulpcore.cli.rpm.distribution import distribution


@main.group()
@pass_pulp_context
def rpm(pulp_ctx: PulpContext) -> None:
    if not pulp_ctx.has_plugin("pulp_rpm"):
        raise click.ClickException("'pulp_rpm' does not seem to be installed.")


rpm.add_command(repository)
repository.add_command(version_group)
rpm.add_command(remote)
rpm.add_command(publication)
rpm.add_command(distribution)
