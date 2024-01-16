import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.python.context import PulpPythonPublicationContext, PulpPythonRepositoryContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    href_option,
    list_command,
    pass_pulp_context,
    publication_filter_options,
    pulp_group,
    resource_option,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="python",
    default_type="python",
    context_table={"python:python": PulpPythonRepositoryContext},
    href_pattern=PulpPythonRepositoryContext.HREF_PATTERN,
)


@pulp_group()
@click.option(
    "-t",
    "--type",
    "publication_type",
    type=click.Choice(["pypi"], case_sensitive=False),
    default="pypi",
)
@pass_pulp_context
@click.pass_context
def publication(ctx: click.Context, pulp_ctx: PulpCLIContext, publication_type: str) -> None:
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
publication.add_command(list_command(decorators=publication_filter_options + [repository_option]))
publication.add_command(show_command(decorators=lookup_options))
publication.add_command(create_command(decorators=create_options))
publication.add_command(destroy_command(decorators=lookup_options))
