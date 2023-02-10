from typing import Any

from pulp_glue.common.context import PluginRequirement
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    load_json_callback,
    pass_pulp_context,
    pulp_group,
    pulp_option,
)

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group()
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
    needs_plugins=[PluginRequirement("core", "3.14.0")],
)
@pulp_option(
    "--protection-time",
    "orphan_protection_time",
    type=int,
    help=_(
        "How long in minutes Pulp should hold orphan Content and Artifacts before becoming"
        " candidates for cleanup task"
    ),
    needs_plugins=[PluginRequirement("core", "3.15.0")],
)
@pass_pulp_context
def cleanup(pulp_ctx: PulpCLIContext, **kwargs: Any) -> None:
    """
    Cleanup orphaned content.
    """
    body = {k: v for k, v in kwargs.items() if v is not None}
    if pulp_ctx.has_plugin(PluginRequirement("core", "3.14.0")):
        result = pulp_ctx.call("orphans_cleanup_cleanup", body=body)
    else:
        result = pulp_ctx.call("orphans_delete")
    pulp_ctx.output_result(result)
