from typing import Any

import click

from pulpcore.cli.common import limit_option, offset_option, PulpContext, PulpEntityContext


class PulpTaskContext(PulpEntityContext):
    HREF: str = "task_href"
    LIST_ID: str = "tasks_list"
    READ_ID: str = "tasks_read"
    CANCEL_ID: str = "tasks_cancel"

    def cancel(self, task_href: str) -> Any:
        return self.pulp_ctx.call(
            self.CANCEL_ID,
            parameters={self.HREF: task_href},
            body={"state": "canceled"},
        )


@click.group()
@click.pass_context
def task(ctx: click.Context) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    ctx.obj = PulpTaskContext(pulp_ctx)


@task.command()
@limit_option
@offset_option
@click.option("--name", help="List only tasks with this name.")
@click.option("--name-contains", "name__contains", help="List only tasks whose name contains this.")
@click.option("--state", help="List only tasks in this state.")
@click.pass_context
def list(ctx: click.Context, limit: int, offset: int, **kwargs: str) -> None:
    """Shows a list of tasks."""
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    task_ctx: PulpTaskContext = ctx.find_object(PulpTaskContext)

    params = {k: v for k, v in kwargs.items() if v is not None}
    result = task_ctx.list(limit=limit, offset=offset, parameters=params)
    pulp_ctx.output_result(result)


@task.command()
@click.option("--href", required=True, help="HREF of the task")
@click.option("-w", "--wait", is_flag=True, help="Wait for the task to finish")
@click.pass_context
def show(ctx: click.Context, href: str, wait: bool) -> None:
    """Shows details of a task."""
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    task_ctx: PulpTaskContext = ctx.find_object(PulpTaskContext)

    entity = task_ctx.show(href)
    if wait and entity["state"] in ["waiting", "running"]:
        click.echo(f"Waiting for task {href} to finish.", err=True)
        entity = pulp_ctx.wait_for_task(entity)
    pulp_ctx.output_result(entity)


@task.command()
@click.option("--href", required=True, help="HREF of the task")
@click.pass_context
def cancel(ctx: click.Context, href: str) -> None:
    """Cancels a task and waits until the cancellation is confirmed."""
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    task_ctx: PulpTaskContext = ctx.find_object(PulpTaskContext)

    entity = task_ctx.show(href)
    if entity["state"] not in ["waiting", "running"]:
        click.ClickException(f"Task {href} is in state {entity['state']} and cannot be canceled.")

    task_ctx.cancel(href)
    click.echo(f"Waiting to cancel task {href}", err=True)
    try:
        pulp_ctx.wait_for_task(entity)
    except Exception as e:
        if str(e) != "Task canceled":
            raise e
    click.echo("Done.")
