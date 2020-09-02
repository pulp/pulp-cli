import click

from pulpcore.cli import main


@main.command()
@click.pass_context
def status(ctx):
    result = ctx.obj.call("status_read")
    ctx.obj.output_result(result)
