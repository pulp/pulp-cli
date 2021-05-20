import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    list_command,
    publication_filter_options,
    resource_option,
    show_command,
)
from pulpcore.cli.rpm.context import PulpRpmPublicationContext, PulpRpmRepositoryContext

_ = gettext.gettext


@click.group()
@click.option(
    "-t",
    "--type",
    "publication_type",
    type=click.Choice(["rpm"], case_sensitive=False),
    default="rpm",
)
@pass_pulp_context
@click.pass_context
def publication(ctx: click.Context, pulp_ctx: PulpContext, publication_type: str) -> None:
    if publication_type == "rpm":
        ctx.obj = PulpRpmPublicationContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option]
create_options = [
    resource_option(
        "--repository",
        default_plugin="rpm",
        default_type="rpm",
        context_table={"rpm:rpm": PulpRpmRepositoryContext},
    ),
    click.option(
        "--version", type=int, help=_("a repository version number, leave blank for latest")
    ),
]

publication.add_command(list_command(decorators=publication_filter_options))
publication.add_command(show_command(decorators=lookup_options))
publication.add_command(create_command(decorators=create_options))
publication.add_command(destroy_command(decorators=lookup_options))
