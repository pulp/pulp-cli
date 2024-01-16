import click
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import PulpCLIContext, pass_pulp_context, pulp_command

translation = get_translation(__package__)
_ = translation.gettext


@pulp_command(name="show")
@click.option("--href", required=True, help=_("HREF of the entry"))
@pass_pulp_context
def show(pulp_ctx: PulpCLIContext, href: str) -> None:
    """Show any resource given its href."""
    # use a random read operation to call the href
    entity = pulp_ctx.call("artifacts_read", parameters={"artifact_href": href})
    pulp_ctx.output_result(entity)
