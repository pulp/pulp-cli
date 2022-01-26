import re
from typing import Any, Optional

import click

from pulpcore.cli.common.context import (
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import list_command, pulp_option
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import PulpTaskContext

translation = get_translation(__name__)
_ = translation.gettext


##############################################################################
# Generic reusable commands


def _task_group_filter_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value is not None:
        pulp_ctx = ctx.find_object(PulpContext)
        assert pulp_ctx is not None

        # Example: "/pulp/api/v3/task-groups/a69230d2-506e-44c7-9c46-e64a905f85e7/"
        match = re.match(
            rf"({pulp_ctx.api_path}task-groups/)?"
            r"([0-9a-f]{8})-?([0-9a-f]{4})-?([0-9a-f]{4})-?([0-9a-f]{4})-?([0-9a-f]{12})/?",
            value,
        )
        if match:
            value = "{}task-groups/{}-{}-{}-{}-{}/".format(
                pulp_ctx.api_path, *match.group(2, 3, 4, 5, 6)
            )
        else:
            raise click.ClickException(_("Either an href or a UUID must be provided."))

    return value


task_filter = [
    click.option("--name", help=_("List only tasks with this name.")),
    click.option(
        "--name-contains",
        "name__contains",
        help=_("List only tasks whose name contains this."),
    ),
    pulp_option(
        "--cid",
        "logging_cid__contains",
        help=_("List only tasks with this correlation id."),
        needs_plugins=[PluginRequirement("core", "3.14.0.dev")],
    ),
    click.option(
        "--state",
        type=click.Choice(
            ["waiting", "skipped", "running", "completed", "failed", "canceled", "canceling"],
            case_sensitive=False,
        ),
        help=_("List only tasks in this state."),
    ),
    click.option(
        "--task-group",
        help=_("List only tasks in this task group. Provide pulp_href or UUID."),
        callback=_task_group_filter_callback,
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
