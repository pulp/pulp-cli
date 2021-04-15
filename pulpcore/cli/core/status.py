import gettext
import time

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context

_ = gettext.gettext


@click.command()
@click.option("--retries", type=int, default=0, help=_("Number of retries before failing."))
@click.option("--retry-delay", type=int, default=1, help=_("Seconds to wait between retries."))
@pass_pulp_context
def status(pulp_ctx: PulpContext, retries: int, retry_delay: int) -> None:
    """
    Retrieve pulp status. And refresh outdated local api caches if server versions changed.
    """
    if retries < 0:
        raise click.ClickException(_("Cannot specify a negative retry count."))
    retries_left = retries
    while True:
        try:
            result = pulp_ctx.call("status_read")
        except click.ClickException:
            if retries_left:
                retries_left = retries_left - 1
                click.echo(".", nl=False, err=True)
                time.sleep(retry_delay)
            else:
                if retries:
                    click.echo(" Failed.", err=True)
                raise
        else:
            if retries:
                click.echo(" Ready.", err=True)
            break

    component_versions = {item["component"]: item["version"] for item in result.get("versions", [])}
    if component_versions != pulp_ctx.component_versions:
        click.echo("Notice: Cached api is outdated. Refreshing...", err=True)
        pulp_ctx.api.load_api(refresh_cache=True)
        result = pulp_ctx.call("status_read")
    pulp_ctx.output_result(result)
