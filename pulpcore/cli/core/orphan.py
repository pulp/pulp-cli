import gettext

import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context

_ = gettext.gettext


@click.group()
def orphan() -> None:
    """
    Handle orphaned content.
    """
    pass


@orphan.command()
@pass_pulp_context
def cleanup(pulp_ctx: PulpContext) -> None:
    """
    Cleanup orphaned content.
    """
    if pulp_ctx.has_plugin(PluginRequirement("core", "3.14")):
        result = pulp_ctx.call("orphans_cleanup_cleanup")
    else:
        result = pulp_ctx.call("orphans_delete")
    pulp_ctx.output_result(result)
