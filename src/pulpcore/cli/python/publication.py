import click

from pulp_glue.common.i18n import get_translation
from pulp_glue.python.context import (
    PulpPythonPublicationContext,
    PulpPythonRepositoryContext,
)

from pulp_cli.generic import (
    create_command,
    destroy_command,
    href_option,
    list_command,
    publication_filter_options,
    pulp_group,
    resource_option,
    show_command,
    type_option,
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
@type_option(choices={"pypi": PulpPythonPublicationContext})
def publication() -> None:
    pass


lookup_options = [href_option]
create_options = [
    repository_option,
    click.option(
        "--version",
        type=int,
        help=_("a repository version number, leave blank for latest"),
    ),
]
publication.add_command(list_command(decorators=publication_filter_options + [repository_option]))
publication.add_command(show_command(decorators=lookup_options))
publication.add_command(create_command(decorators=create_options))
publication.add_command(destroy_command(decorators=lookup_options))
