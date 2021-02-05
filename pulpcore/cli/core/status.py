import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context

_ = gettext.gettext


@click.command()
@pass_pulp_context
def status(pulp_ctx: PulpContext) -> None:
    """
    Retrieve pulp status. And refresh outdated local api caches if server versions changed.
    """
    result = pulp_ctx.call("status_read")
    component_versions = {item["component"]: item["version"] for item in result.get("versions", [])}
    if component_versions != pulp_ctx.component_versions:
        click.echo("Notice: Cached api is outdated. Refreshing...", err=True)
        pulp_ctx.api.load_api(refresh_cache=True)
        result = pulp_ctx.call("status_read")
    pulp_ctx.output_result(result)
