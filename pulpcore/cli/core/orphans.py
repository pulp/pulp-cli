import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context

_ = gettext.gettext


@click.group(deprecated=True)
def orphans() -> None:
    """
    Use 'pulp orphan' instead.
    """
    pass


@orphans.command(deprecated=True)
@pass_pulp_context
def delete(pulp_ctx: PulpContext) -> None:
    """
    Use pulp 'orphan cleanup' instead.
    """
    result = pulp_ctx.call("orphans_delete")
    pulp_ctx.output_result(result)
