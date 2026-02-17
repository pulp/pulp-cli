import click

from pulp_glue.common.i18n import get_translation

from pulp_cli.generic import PulpCLIContext, pass_pulp_context, pulp_command

translation = get_translation(__package__)
_ = translation.gettext


@pulp_command(name="show")
@click.option("--href", default=None, help=_("HREF of the resource"))
@click.option("--prn", default=None, help=_("PRN of the resource"))
@pass_pulp_context
def show(pulp_ctx: PulpCLIContext, /, href: str | None, prn: str | None) -> None:
    """Show any resource given its href or prn."""
    if (href is None) == (prn is None):
        raise click.UsageError(_("Either href or prn needs to be provided."))
    if href is not None:
        # Use a random read operation to call the href.
        # This is doomed to fail if we ever start validating responses.
        entity = pulp_ctx.call("artifacts_read", parameters={"artifact_href": href})
    else:
        assert prn is not None
        entity_ctx = pulp_ctx.resolve_prn(prn)
        entity = entity_ctx.entity
    pulp_ctx.output_result(entity)
