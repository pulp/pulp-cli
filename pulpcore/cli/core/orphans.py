from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import PulpCLIContext, pass_pulp_context, pulp_group

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group(deprecated=True)
def orphans() -> None:
    """
    Use 'pulp orphan' instead.
    """
    pass


@orphans.command(deprecated=True)
@pass_pulp_context
def delete(pulp_ctx: PulpCLIContext) -> None:
    """
    Use pulp 'orphan cleanup' instead.
    """
    result = pulp_ctx.call("orphans_delete")
    pulp_ctx.output_result(result)
