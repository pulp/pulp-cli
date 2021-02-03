import gettext
from typing import Any

import click

from pulpcore.cli.common.context import (
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import list_command
from pulpcore.cli.core.context import PulpTaskContext

_ = gettext.gettext


##############################################################################
# Generic reusable commands


task_filter = [
    click.option("--name", help=_("List only tasks with this name.")),
    click.option(
        "--name-contains",
        "name__contains",
        help=_("List only tasks whose name contains this."),
    ),
    click.option(
        "--state",
        type=click.Choice(
            ["waiting", "skipped", "running", "completed", "failed", "canceled"],
            case_sensitive=False,
        ),
        help=_("List only tasks in this state."),
    ),
]


def task_command(**kwargs: Any) -> click.Command:
    """A factory that creates a nested task command group."""

    # This generic moved to core to avoid a circular import

    if "name" not in kwargs:
        kwargs["name"] = "task"
    decorators = kwargs.pop("decorators", [])

    @click.group(**kwargs)
    @pass_entity_context
    @pass_pulp_context
    @click.pass_context
    def callback(
        ctx: click.Context,
        pulp_ctx: PulpContext,
        entity_ctx: PulpEntityContext,
    ) -> None:
        ctx.obj = PulpTaskContext(pulp_ctx)
        ctx.obj.resource_context = entity_ctx

    callback.add_command(list_command(decorators=task_filter + decorators))

    return callback
