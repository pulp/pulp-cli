import gettext

import click

from pulpcore.cli.ansible.context import PulpAnsibleCollectionVersionContext, PulpAnsibleRoleContext
from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import list_command

_ = gettext.gettext


@click.group()
@click.option(
    "-t",
    "--type",
    "content_type",
    type=click.Choice(["collection-version", "role"], case_sensitive=False),
    default="collection-version",
)
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpContext, content_type: str) -> None:
    if content_type == "collection-version":
        ctx.obj = PulpAnsibleCollectionVersionContext(pulp_ctx)
    elif content_type == "role":
        ctx.obj = PulpAnsibleRoleContext(pulp_ctx)
    else:
        raise NotImplementedError()


content.add_command(list_command())
