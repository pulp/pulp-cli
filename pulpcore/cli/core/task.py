import click

from pulpcore.cli.common import main, PulpContext


@main.group()
@click.pass_context
def task(ctx: click.Context) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    pulp_ctx.href_key = "task_href"
    pulp_ctx.list_id = "tasks_list"
    pulp_ctx.cancel_id = "tasks_cancel"


@task.command()
@click.option("--name")
@click.option("--name-contains", "name__contains")
@click.option("--state")
@click.pass_context
def list(ctx: click.Context, **kwargs: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    assert pulp_ctx.list_id is not None
    params = {k: v for k, v in kwargs.items() if v is not None}
    result = pulp_ctx.call(pulp_ctx.list_id, parameters=params)
    pulp_ctx.output_result(result)


@task.command()
@click.option("--href", required=True)
@click.pass_context
def cancel(ctx: click.Context, href: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    assert pulp_ctx.cancel_id is not None
    pulp_ctx.call(
        pulp_ctx.cancel_id,
        parameters={pulp_ctx.href_key: href},
        body={"state": "canceled"},
    )
    click.echo(f"Waiting to cancel task {href}", err=True)
    try:
        pulp_ctx.wait_for_task(href)
    except Exception as e:
        if str(e) != "Task canceled":
            raise e
    click.echo("Done.")
