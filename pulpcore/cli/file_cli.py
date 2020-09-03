import click

from pulpcore.cli import main
from pulpcore.cli.file.repository import repository
from pulpcore.cli.file.repository_version import version
from pulpcore.cli.file.remote import remote
from pulpcore.cli.file.publication import publication
from pulpcore.cli.file.distribution import distribution


@main.group()
@click.pass_context
def file(ctx):
    pass


# TODO: figure out how we want to load/organize these commands
file.add_command(repository)
file.add_command(version)
file.add_command(remote)
file.add_command(publication)
file.add_command(distribution)
