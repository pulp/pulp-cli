import gettext
import sys

import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context

_ = gettext.gettext


@click.group()
def debug() -> None:
    """
    Commands useful for debugging.
    """


@debug.command()
@click.option("--name", required=True)
@click.option("--min-version", help=_("Succeed only if the installed version is not smaller."))
@click.option("--max-version", help=_("Succeed only if the installed version is smaller."))
@pass_pulp_context
def has_plugin(pulp_ctx: PulpContext, name: str, min_version: str, max_version: str) -> None:
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

    result = {}
    for state in ["waiting", "skipped", "running", "completed", "failed", "canceled", "canceling"]:
        payload = {"limit": 0, "state": state}
        answer = pulp_ctx.call(PulpTaskContext.LIST_ID, parameters=payload)
        result[state] = answer["count"]
    pulp_ctx.output_result(result)
