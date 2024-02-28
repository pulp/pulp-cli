import re
import typing as t

import click
from pulp_glue.common.context import DATETIME_FORMATS, PluginRequirement, PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpTaskContext, PulpWorkerContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    list_command,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    pulp_option,
    resource_option,
)

translation = get_translation(__package__)
_ = translation.gettext


##############################################################################
# Generic reusable commands


class HrefOrUuidCallback:
    def __init__(self, base_href: str) -> None:
        self.base_href = base_href

    def __call__(
        self, ctx: click.Context, param: click.Parameter, value: t.Optional[str]
    ) -> t.Optional[str]:
        if value is not None:
            pulp_ctx = ctx.find_object(PulpCLIContext)
            assert pulp_ctx is not None

            # Example: "/pulp/api/v3/tasks/a69230d2-506e-44c7-9c46-e64a905f85e7/"
            href_match = re.match(
                rf"({pulp_ctx.api_path}{self.base_href}/)?"
                r"([0-9a-f]{8})-?([0-9a-f]{4})-?([0-9a-f]{4})-?([0-9a-f]{4})-?([0-9a-f]{12})/?",
                value,
            )
            if href_match:
                value = "{}{}/{}-{}-{}-{}-{}/".format(
                    pulp_ctx.api_path, self.base_href, *href_match.group(2, 3, 4, 5, 6)
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
        needs_plugins=[PluginRequirement("core", specifier=">=3.14.0")],
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
        "--state-in",
        "state__in",
        type=click.Choice(
            ["waiting", "skipped", "running", "completed", "failed", "canceled", "canceling"],
            case_sensitive=False,
        ),
        multiple=True,
        help=_("List only tasks in one of these states. Can be specified multiple times."),
    ),
    click.option(
        "--task-group",
        help=_("List only tasks in this task group. Provide pulp_href or UUID."),
        callback=HrefOrUuidCallback("task-groups"),
    ),
    click.option(
        "--parent-task",
        help=_("Parent task by uuid or href."),
        callback=HrefOrUuidCallback("tasks"),
    ),
    resource_option(
        "--worker",
        default_plugin="core",
        default_type="none",
        context_table={"core:none": PulpWorkerContext},
        href_pattern=PulpWorkerContext.HREF_PATTERN,
        help=_("Worker used to execute the task by name or href."),
    ),
    click.option(
        "--created-resource",
        "created_resources",
        help=_("Href of a resource created in the task."),
    ),
    click.option(
        "--started-after",
        "started_at__gte",
        help=_("Filter for tasks started at or after this date"),
        type=click.DateTime(formats=DATETIME_FORMATS),
    ),
    click.option(
        "--started-before",
        "started_at__lte",
        help=_("Filter for tasks started at or before this date"),
        type=click.DateTime(formats=DATETIME_FORMATS),
    ),
    click.option(
        "--finished-after",
        "finished_at__gte",
        help=_("Filter for tasks finished at or after this date"),
        type=click.DateTime(formats=DATETIME_FORMATS),
    ),
    click.option(
        "--finished-before",
        "finished_at__lte",
        help=_("Filter for tasks finished at or before this date"),
        type=click.DateTime(formats=DATETIME_FORMATS),
    ),
]


def task_command(**kwargs: t.Any) -> click.Command:
    """A factory that creates a nested task command group."""

    # This generic moved to core to avoid a circular import

    if "name" not in kwargs:
        kwargs["name"] = "task"
    decorators = kwargs.pop("decorators", [])

    @pulp_group(**kwargs)
    @pass_entity_context
    @pass_pulp_context
    @click.pass_context
    def callback(
        ctx: click.Context,
        pulp_ctx: PulpCLIContext,
        entity_ctx: PulpEntityContext,
    ) -> None:
        ctx.obj = PulpTaskContext(pulp_ctx)
        ctx.obj.resource_context = entity_ctx

    callback.add_command(list_command(decorators=task_filter + decorators))

    return callback
