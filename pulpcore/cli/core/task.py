import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_entity_context, pass_pulp_context
from pulpcore.cli.common.generic import list_command
from pulpcore.cli.core.context import PulpTaskContext
from pulpcore.cli.core.generic import task_filter

_ = gettext.gettext


@click.group()
@pass_pulp_context
@click.pass_context
def task(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpTaskContext(pulp_ctx)


task.add_command(list_command(decorators=task_filter))


@task.command()
@click.option("--href", required=True, help=_("HREF of the task"))
@click.option("-w", "--wait", is_flag=True, help=_("Wait for the task to finish"))
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
@click.option("--href", required=True, help=_("HREF of the task"))
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
