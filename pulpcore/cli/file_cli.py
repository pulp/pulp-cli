import click

from pulpcore.cli import main
from pulpcore.cli.file.repository import repository
from pulpcore.cli.file.remote import remote


@main.group()
@click.pass_context
def file(ctx):
    pass


# TODO: figure out how we want to load/organize these commands
file.add_command(repository)
file.add_command(remote)
