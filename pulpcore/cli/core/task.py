from typing import Any, Dict

import click

from pulpcore.cli.common import PulpContext


class PulpTaskContext:
    def __init__(self, pulp_ctx: PulpContext) -> None:
        self.pulp_ctx: PulpContext = pulp_ctx

    def list(self, parameters: Dict[str, str]) -> Any:
        return self.pulp_ctx.call("tasks_list", parameters=parameters)

    def show(self, task_href: str) -> Any:
        return self.pulp_ctx.call("tasks_read", parameters={"task_href": task_href})

    def cancel(self, task_href: str) -> Any:
        return self.pulp_ctx.call(
            "tasks_cancel",
            parameters={"task_href": task_href},
            body={"state": "canceled"},
        )


@click.group()
@click.pass_context
def task(ctx: click.Context) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    ctx.obj = PulpTaskContext(pulp_ctx)


@task.command()
@click.option("--name")
@click.option("--name-contains", "name__contains")
@click.option("--state")
@click.pass_context
def list(ctx: click.Context, **kwargs: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    task_ctx: PulpTaskContext = ctx.find_object(PulpTaskContext)

    params = {k: v for k, v in kwargs.items() if v is not None}
    result = task_ctx.list(parameters=params)
    pulp_ctx.output_result(result)


@task.command()
@click.option("--href", required=True)
@click.option("-w", "--wait", is_flag=True)
@click.pass_context
def show(ctx: click.Context, href: str, wait: bool) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    task_ctx: PulpTaskContext = ctx.find_object(PulpTaskContext)

    entity = task_ctx.show(href)
    if wait and entity["state"] in ["waiting", "running"]:
        click.echo(f"Waiting for task {href} to finish.", err=True)
        entity = pulp_ctx.wait_for_task(href)
    pulp_ctx.output_result(entity)


@task.command()
@click.option("--href", required=True)
@click.pass_context
def cancel(ctx: click.Context, href: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    task_ctx: PulpTaskContext = ctx.find_object(PulpTaskContext)

    entity = task_ctx.show(href)
    if entity["state"] not in ["waiting", "running"]:
        click.ClickException(f"Task {href} is in state {entity['state']} and cannot be canceled.")

    task_ctx.cancel(href)
    click.echo(f"Waiting to cancel task {href}", err=True)
    try:
        pulp_ctx.wait_for_task(href)
    except Exception as e:
        if str(e) != "Task canceled":
            raise e
    click.echo("Done.")
