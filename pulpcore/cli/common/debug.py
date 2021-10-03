import gettext
import sys
from typing import Optional

import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context

_ = gettext.gettext


@click.group(help=_("Commands useful for debugging"))
def debug() -> None:
    """
    Commands useful for debugging.
    """


@debug.command()
@click.option("--name", required=True)
@click.option("--min-version", help=_("Succeed only if the installed version is not smaller."))
@click.option("--max-version", help=_("Succeed only if the installed version is smaller."))
@pass_pulp_context
def has_plugin(
    pulp_ctx: PulpContext, name: str, min_version: Optional[str], max_version: Optional[str]
) -> None:
    """
    Check whether a specific plugin is installed on the server.
    """
    available = pulp_ctx.has_plugin(PluginRequirement(name, min_version, max_version))
    pulp_ctx.output_result(available)
    sys.exit(0 if available else 1)


@debug.command()
@pass_pulp_context
def task_summary(pulp_ctx: PulpContext) -> None:
    """
    List a summary of tasks by status.
    """
    from pulpcore.cli.core.context import PulpTaskContext

    TASK_STATES = ["waiting", "skipped", "running", "completed", "failed", "canceled"]
    if pulp_ctx.has_plugin(PluginRequirement("core", min="3.14")):
        TASK_STATES.append("canceling")
    result = {}
    for state in TASK_STATES:
        payload = {"limit": 1, "state": state}
        answer = pulp_ctx.call(PulpTaskContext.LIST_ID, parameters=payload)
        result[state] = answer["count"]
    pulp_ctx.output_result(result)


@debug.group(name="openapi")
def openapi_group() -> None:
    pass


@openapi_group.command()
@pass_pulp_context
def schema(pulp_ctx: PulpContext) -> None:
    """
    Print the openapi schema of the server.
    """
    pulp_ctx.output_result(pulp_ctx.api.api_spec)


@openapi_group.command()
@click.option("--id", "operation_id", required=True)
@pass_pulp_context
def operation(pulp_ctx: PulpContext, operation_id: str) -> None:
    """
    Print the openapi schema of the server.
    """
    method: str
    path: str
    method, path = pulp_ctx.api.operations[operation_id]
    result = {
        "method": method,
        "path": path,
        "operation": pulp_ctx.api.api_spec["paths"][path][method],
    }
    pulp_ctx.output_result(result)


@openapi_group.command()
@pass_pulp_context
def operation_ids(pulp_ctx: PulpContext) -> None:
    pulp_ctx.output_result(list(pulp_ctx.api.operations.keys()))
