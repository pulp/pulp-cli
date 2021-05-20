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
from pulpcore.cli.python.context import PulpPythonPublicationContext, PulpPythonRepositoryContext

_ = gettext.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="python",
    default_type="python",
    context_table={"python:python": PulpPythonRepositoryContext},
)


@click.group()
@click.option(
    "-t",
    "--type",
    "publication_type",
    type=click.Choice(["pypi"], case_sensitive=False),
    default="pypi",
)
@pass_pulp_context
@click.pass_context
def publication(ctx: click.Context, pulp_ctx: PulpContext, publication_type: str) -> None:
    if publication_type == "pypi":
        ctx.obj = PulpPythonPublicationContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option]
create_options = [
    repository_option,
    click.option(
        "--version", type=int, help=_("a repository version number, leave blank for latest")
    ),
]
publication.add_command(list_command(decorators=publication_filter_options))
publication.add_command(show_command(decorators=lookup_options))
publication.add_command(create_command(decorators=create_options))
publication.add_command(destroy_command(decorators=lookup_options))
