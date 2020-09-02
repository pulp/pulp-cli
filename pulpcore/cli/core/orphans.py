import click


@click.group()
@click.pass_context
def orphans(ctx):
    pass


@orphans.command()
@click.pass_context
def delete(ctx):
    result = ctx.obj.call("orphans_delete")
    ctx.obj.output_result(result)
