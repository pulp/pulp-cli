import gettext
from typing import Optional

import click

from pulpcore.cli.common.context import (
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import href_option, list_command, pulp_option
from pulpcore.cli.core.context import PulpTaskContext
from pulpcore.cli.core.generic import task_filter

_ = gettext.gettext


def _uuid_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.pulp_href = f"/pulp/api/v3/tasks/{value}/"
    return value


uuid_option = pulp_option(
    "--uuid",
    help=_("UUID of the {entity}"),
    callback=_uuid_callback,
    expose_value=False,
)


@click.group()
@pass_pulp_context
@click.pass_context
def task(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpTaskContext(pulp_ctx)


task.add_command(list_command(decorators=task_filter))


@task.command()
@href_option
@uuid_option
@click.option("-w", "--wait", is_flag=True, help=_("Wait for the task to finish"))
@pass_entity_context
@pass_pulp_context
def show(pulp_ctx: PulpContext, task_ctx: PulpTaskContext, wait: bool) -> None:
    """Shows details of a task."""
    entity = task_ctx.entity
    if wait and entity["state"] in ["waiting", "running", "canceling"]:
        click.echo(
            _("Waiting for task {href} to finish.").format(href=task_ctx.pulp_href), err=True
        )
        entity = pulp_ctx.wait_for_task(entity)
    pulp_ctx.output_result(entity)


@task.command()
@href_option
@uuid_option
@pass_entity_context
@pass_pulp_context
def cancel(pulp_ctx: PulpContext, task_ctx: PulpTaskContext) -> None:
    """Cancels a task and waits until the cancellation is confirmed."""
    entity = task_ctx.entity
    if entity["state"] not in ["waiting", "running"]:
        click.ClickException(
            _("Task {href} is in state {state} and cannot be canceled.").format(
                href=task_ctx.pulp_href, state=entity["state"]
            )
        )

    task_ctx.cancel(task_ctx.pulp_href)
    click.echo(_("Waiting to cancel task {href}").format(href=task_ctx.pulp_href), err=True)
    try:
        pulp_ctx.wait_for_task(entity)
    except Exception as e:
        if str(e) != "Task canceled":
            raise e
    click.echo(_("Done."), err=True)
