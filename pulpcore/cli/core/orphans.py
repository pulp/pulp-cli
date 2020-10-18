import click

from pulpcore.cli.common import PulpContext


@click.group()
def orphans() -> None:
    pass


@orphans.command()
@click.pass_context
def delete(ctx: click.Context) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    result = pulp_ctx.call("orphans_delete")
    pulp_ctx.output_result(result)
