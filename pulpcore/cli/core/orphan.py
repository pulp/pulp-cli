from typing import Any

import click
from pulp_glue.common.context import PluginRequirement
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpOrphanContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    load_json_callback,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    pulp_option,
)

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group()
@pass_pulp_context
@click.pass_context
def orphan(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    """
    Handle orphaned content.
    """
    ctx.obj = PulpOrphanContext(pulp_ctx)


@orphan.command()
@pulp_option(
    "--content-hrefs",
    help=_("List of specific Contents to delete if they are orphans"),
    callback=load_json_callback,
    needs_plugins=[PluginRequirement("core", specifier=">=3.14.0")],
)
@pulp_option(
    "--protection-time",
    "orphan_protection_time",
    type=int,
    help=_(
        "How long in minutes Pulp should hold orphan Content and Artifacts before becoming"
        " candidates for cleanup task"
    ),
    needs_plugins=[PluginRequirement("core", specifier=">=3.15.0")],
)
@pass_entity_context
@pass_pulp_context
def cleanup(pulp_ctx: PulpCLIContext, orphan_ctx: PulpOrphanContext, **kwargs: Any) -> None:
    """
    Cleanup orphaned content.
    """
    pulp_ctx.output_result(orphan_ctx.cleanup(kwargs))
