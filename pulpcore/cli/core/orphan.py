from typing import Any

import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import load_json_callback, pulp_option
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


@click.group()
def orphan() -> None:
    """
    Handle orphaned content.
    """
    pass


@orphan.command()
@pulp_option(
    "--content-hrefs",
    help=_("List of specific Contents to delete if they are orphans"),
    callback=load_json_callback,
    needs_plugins=[PluginRequirement("core", "3.14")],
)
@pulp_option(
    "--protection-time",
    "orphan_protection_time",
    type=int,
    help=_(
        "How long in minutes Pulp should hold orphan Content and Artifacts before becoming"
        " candidates for cleanup task"
    ),
    needs_plugins=[PluginRequirement("core", "3.15")],
)
@pass_pulp_context
def cleanup(pulp_ctx: PulpContext, **kwargs: Any) -> None:
    """
    Cleanup orphaned content.
    """
    body = {k: v for k, v in kwargs.items() if v is not None}
    if pulp_ctx.has_plugin(PluginRequirement("core", "3.14")):
        result = pulp_ctx.call("orphans_cleanup_cleanup", body=body)
    else:
        result = pulp_ctx.call("orphans_delete")
    pulp_ctx.output_result(result)
