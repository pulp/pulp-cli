from typing import Any, Dict, List

import click

from pulpcore.cli.common import DEFAULT_LIMIT, BATCH_SIZE, PulpContext


class PulpTaskContext:
    def __init__(self, pulp_ctx: PulpContext) -> None:
        self.pulp_ctx: PulpContext = pulp_ctx

    def list(self, limit: int, offset: int, parameters: Dict[str, Any]) -> List[Any]:
        count: int = -1
        entities: List[Any] = []
        payload: Dict[str, Any] = parameters.copy()
        payload["offset"] = offset
        payload["limit"] = BATCH_SIZE
        while limit != 0:
            if limit > BATCH_SIZE:
                limit -= BATCH_SIZE
            else:
                payload["limit"] = limit
                limit = 0
            result: Dict[str, Any] = self.pulp_ctx.call("tasks_list", parameters=payload)
            count = result["count"]
            entities.extend(result["results"])
            if result["next"] is None:
                break
            payload["offset"] += payload["limit"]
        else:
            click.echo(f"Not all {count} entries were shown.", err=True)
        return entities

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
@click.option("--limit", default=DEFAULT_LIMIT, type=int, help="Limit the number of tasks to show.")
@click.option("--offset", default=0, type=int, help="Skip a number of tasks to show.")
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
        entity = pulp_ctx.wait_for_task(href)
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
        pulp_ctx.wait_for_task(href)
    except Exception as e:
        if str(e) != "Task canceled":
            raise e
    click.echo("Done.")
