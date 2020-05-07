import click
import pkgutil
from pulpcore.client.pulpcore import StatusApi

from pulpcore.cli import main


@main.command()
@click.pass_context
def status(ctx):
    status_api = StatusApi(ctx.obj.core_client)
    result = status_api.status_read()
    click.echo(result)
