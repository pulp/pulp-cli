import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context

_ = gettext.gettext


@click.group()
def orphans() -> None:
    pass


@orphans.command()
@pass_pulp_context
def delete(pulp_ctx: PulpContext) -> None:
    result = pulp_ctx.call("orphans_delete")
    pulp_ctx.output_result(result)
