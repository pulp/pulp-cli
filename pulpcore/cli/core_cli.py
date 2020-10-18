import click

from pulpcore.cli.common import main, PulpContext
from pulpcore.cli.core.artifact import artifact
from pulpcore.cli.core.orphans import orphans
from pulpcore.cli.core.task import task


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    result = pulp_ctx.call("status_read")
    pulp_ctx.output_result(result)


main.add_command(artifact)
main.add_command(orphans)
main.add_command(task)
