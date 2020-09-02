import click

from pulpcore.cli import main


@main.group()
@click.pass_context
def task(ctx):
    ctx.obj.href_key = "task_href"
    ctx.obj.href = "task_href"
    ctx.obj.list_id = "tasks_list"
    ctx.obj.cancel_id = "tasks_cancel"


@task.command()
@click.option("--name")
@click.option("--name-contains", "name__contains")
@click.option("--state")
@click.pass_context
def list(ctx, **kwargs):
    params = {k: v for k, v in kwargs.items() if v is not None}
    result = ctx.obj.call(ctx.obj.list_id, parameters=params)
    ctx.obj.output_result(result)


@task.command()
@click.option("--href")
@click.pass_context
def cancel(ctx, href):
    ctx.obj.call(
        ctx.obj.cancel_id,
        parameters={ctx.obj.href_key: href},
        body={"state": "canceled"},
    )
    click.echo(f"Waiting to cancel task {href}", err=True)
    try:
        ctx.obj.wait_for_task(href)
    except Exception as e:
        if str(e) != "Task canceled":
            raise e
    click.echo("Done.")
