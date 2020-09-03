import click

from pulpcore.cli import main


@main.group()
@click.pass_context
def orphans(ctx):
    pass


@orphans.command()
@click.pass_context
def delete(ctx):
    result = ctx.obj.call("orphans_delete")
    ctx.obj.output_result(result)


@main.command()
@click.pass_context
def status(ctx):
    result = ctx.obj.call("status_read")
    ctx.obj.output_result(result)
