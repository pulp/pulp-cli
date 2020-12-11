from copy import deepcopy
import click

from pulpcore.cli.common.generic import (
    list_entities,
)
from pulpcore.cli.common.context import (
    pass_pulp_context,
    pass_entity_context,
    PulpContext,
)
from pulpcore.cli.core.context import (
    PulpTaskContext,
)


@click.group()
@pass_pulp_context
@click.pass_context
def task(ctx: click.Context, pulp_ctx: PulpContext) -> None:
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
@pass_entity_context
@pass_pulp_context
def show(pulp_ctx: PulpContext, task_ctx: PulpTaskContext, href: str, wait: bool) -> None:
    """Shows details of a task."""
    entity = task_ctx.show(href)
    if wait and entity["state"] in ["waiting", "running"]:
        click.echo(f"Waiting for task {href} to finish.", err=True)
        entity = pulp_ctx.wait_for_task(entity)
    pulp_ctx.output_result(entity)


@task.command()
@click.option("--href", required=True, help="HREF of the task")
@pass_entity_context
@pass_pulp_context
def cancel(pulp_ctx: PulpContext, task_ctx: PulpTaskContext, href: str) -> None:
    """Cancels a task and waits until the cancellation is confirmed."""
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
    click.echo("Done.", err=True)
