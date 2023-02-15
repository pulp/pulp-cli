import re
from contextlib import suppress
from datetime import datetime
from typing import Optional, Tuple

import click
from pulp_glue.common.context import DATETIME_FORMATS, PluginRequirement, PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpTaskContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    destroy_command,
    href_option,
    list_command,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    pulp_option,
    role_command,
)
from pulpcore.cli.core.generic import task_filter

translation = get_translation(__name__)
_ = translation.gettext


def _uuid_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.pulp_href = f"{entity_ctx.pulp_ctx.api_path}tasks/{value}/"
    return value


uuid_option = pulp_option(
    "--uuid",
    help=_("UUID of the {entity}"),
    callback=_uuid_callback,
    expose_value=False,
)


@pulp_group()
@pass_pulp_context
@click.pass_context
def task(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpTaskContext(pulp_ctx)


task.add_command(
    list_command(
        decorators=task_filter
        + [
            pulp_option(
                "--reserved-resource",
                "reserved_resources",
                help=_("Href of a resource reserved by the task."),
            ),
            pulp_option(
                "--reserved-resource-in",
                "reserved_resources__in",
                multiple=True,
                help=_("Href of a resource reserved by the task. May be specified multiple times."),
                needs_plugins=[PluginRequirement("core", min="3.22.0dev")],
            ),
            pulp_option(
                "--exclusive-resource",
                "exclusive_resources",
                help=_("Href of a resource reserved exclusively by the task."),
            ),
            pulp_option(
                "--exclusive-resource-in",
                "exclusive_resources__in",
                multiple=True,
                help=_(
                    "Href of a resource reserved exclusively by the task."
                    " May be specified multiple times."
                ),
                needs_plugins=[PluginRequirement("core", min="3.22.0dev")],
            ),
            pulp_option(
                "--shared-resource",
                "shared_resources",
                help=_("Href of a resource shared by the task."),
            ),
            pulp_option(
                "--shared-resource-in",
                "shared_resources__in",
                multiple=True,
                help=_("Href of a resource shared by the task. May be specified multiple times."),
                needs_plugins=[PluginRequirement("core", min="3.22.0dev")],
            ),
        ]
    )
)
task.add_command(destroy_command(decorators=[href_option, uuid_option]))
task.add_command(
    role_command(
        decorators=[href_option, uuid_option],
        needs_plugins=[PluginRequirement("core", min="3.17.0")],
    )
)


@task.command()
@href_option
@uuid_option
@click.option("-w", "--wait", is_flag=True, help=_("Wait for the task to finish"))
@pass_entity_context
@pass_pulp_context
def show(pulp_ctx: PulpCLIContext, task_ctx: PulpTaskContext, wait: bool) -> None:
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
@click.option(
    "--all", "all_tasks", is_flag=True, help=_("Cancel all 'waiting' and 'running' tasks.")
)
@click.option("--waiting", "waiting_tasks", is_flag=True, help=_("Cancel all 'waiting' tasks."))
@click.option("--running", "running_tasks", is_flag=True, help=_("Cancel all 'running' tasks."))
@pass_entity_context
@pass_pulp_context
def cancel(
    pulp_ctx: PulpCLIContext,
    task_ctx: PulpTaskContext,
    all_tasks: bool,
    waiting_tasks: bool,
    running_tasks: bool,
) -> None:
    """Cancels a task and waits until the cancellation is confirmed."""
    states = []
    if waiting_tasks or all_tasks:
        states.append("waiting")
    if running_tasks or all_tasks:
        states.append("running")
    if states:
        tasks = task_ctx.list(limit=1 << 64, offset=0, parameters={"state__in": states})
        for task in tasks:
            with suppress(Exception):
                task_ctx.cancel(task["pulp_href"])
        for task in tasks:
            with suppress(Exception):
                pulp_ctx.wait_for_task(task)
    else:
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
            if not re.match(rf"Task {pulp_ctx.api_path}tasks/[-0-9a-f]*/ canceled", str(e)):
                raise e
        click.echo(_("Done."), err=True)


@task.command()
@click.option(
    "--finished-before",
    "finished",
    help=_("Purge task-records whose 'finished' time is **before** the time specified."),
    type=click.DateTime(formats=DATETIME_FORMATS),
)
@click.option(
    "--state",
    help=_("Only purge tasks in the specified state(s). Can be specified multiple times."),
    type=click.Choice(["skipped", "completed", "failed", "canceled"]),
    multiple=True,
)
@pass_entity_context
@pass_pulp_context
def purge(
    pulp_ctx: PulpCLIContext,
    task_ctx: PulpTaskContext,
    finished: Optional[datetime],
    state: Optional[Tuple[str]],
) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("core", "3.17.0"))
    state_list = list(state) if state else None
    task_ctx.purge(finished, state_list)


@task.command()
@pass_entity_context
@pass_pulp_context
def summary(pulp_ctx: PulpCLIContext, task_ctx: PulpTaskContext) -> None:
    """
    List a summary of tasks by status.
    """
    result = task_ctx.summary()
    pulp_ctx.output_result(result)
