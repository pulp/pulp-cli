import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context

_ = gettext.gettext


@click.command(name="show")
@click.option("--href", required=True, help=_("HREF of the entry"))
@pass_pulp_context
def show(pulp_ctx: PulpContext, href: str) -> None:
    """Show any resource given its href."""
    # use a random read operation to call the href
    entity = pulp_ctx.call("artifacts_read", parameters={"artifact_href": href})
    pulp_ctx.output_result(entity)
