from typing import Any

from copy import deepcopy
import click

from pulpcore.cli.common import list_entities, PulpContext, PulpEntityContext


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


# deepcopy to not effect other list subcommands
list_tasks = deepcopy(list_entities)
click.option("--name", help="List only tasks with this name.")(list_tasks)
click.option("--name-contains", "name__contains", help="List only tasks whose name contains this.")(
    list_tasks
)
click.option("--state", help="List only tasks in this state.")(list_tasks)
task.add_command(list_tasks)


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
