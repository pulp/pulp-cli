import typing as t

import click
from pulp_glue.common.context import PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpTaskGroupContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    href_option,
    list_command,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    pulp_option,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def task_group(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpTaskGroupContext(pulp_ctx)


task_group.add_command(list_command())


def _uuid_callback(
    ctx: click.Context, param: click.Parameter, value: t.Optional[str]
) -> t.Optional[str]:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.pulp_href = f"{entity_ctx.pulp_ctx.api_path}task-groups/{value}/"
    return value


uuid_option = pulp_option(
    "--uuid",
    help=_("UUID of the {entity}"),
    callback=_uuid_callback,
    expose_value=False,
)


@task_group.command()
@href_option
@uuid_option
@click.option("-w", "--wait", is_flag=True, help=_("Wait for the group-task to finish"))
@pass_entity_context
@pass_pulp_context
def show(pulp_ctx: PulpCLIContext, task_group_ctx: PulpEntityContext, wait: bool) -> None:
    """Shows details of a group-task."""
    assert isinstance(task_group_ctx, PulpTaskGroupContext)

    entity = task_group_ctx.entity
    if wait:
        if not entity["all_tasks_dispatched"]:
            click.echo(_("Waiting for all tasks to be dispatched"), err=True)
        else:
            unfinished_tasks = []
            for task in entity["tasks"]:
                if task["state"] in ["waiting", "running", "canceling"]:
                    unfinished_tasks.append(task["pulp_href"])

            if unfinished_tasks:
                click.echo(
                    _("Waiting for the following tasks to finish: {}").format(unfinished_tasks),
                    err=True,
                )

        entity = pulp_ctx.wait_for_task_group(entity)
    pulp_ctx.output_result(entity)
