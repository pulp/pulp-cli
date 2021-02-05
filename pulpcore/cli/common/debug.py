import gettext
import sys

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context

_ = gettext.gettext


@click.group()
def debug() -> None:
    """
    Commands useful for debugging.
    """


@debug.command()
@click.option("--name", required=True)
@click.option("--min-version")
@click.option("--max-version")
@pass_pulp_context
def has_plugin(pulp_ctx: PulpContext, name: str, min_version: str, max_version: str) -> None:
    available = pulp_ctx.has_plugin(name, min_version, max_version)
    pulp_ctx.output_result(available)
    sys.exit(0 if available else 1)
