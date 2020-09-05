import click

from pulpcore.cli import main
from pulpcore.cli.core.artifact import artifact
from pulpcore.cli.core.orphans import orphans
from pulpcore.cli.core.task import task


@main.command()
@click.pass_context
def status(ctx):
    result = ctx.obj.call("status_read")
    ctx.obj.output_result(result)


main.add_command(artifact)
main.add_command(orphans)
main.add_command(task)
