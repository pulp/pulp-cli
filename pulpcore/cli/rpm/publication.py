import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    list_command,
    publication_filter_options,
    pulp_group,
    resource_option,
    show_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.rpm.context import PulpRpmPublicationContext, PulpRpmRepositoryContext

translation = get_translation(__name__)
_ = translation.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="rpm",
    default_type="rpm",
    context_table={"rpm:rpm": PulpRpmRepositoryContext},
)


@pulp_group()
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
    repository_option,
    click.option(
        "--version", type=int, help=_("a repository version number, leave blank for latest")
    ),
]
filter_options = publication_filter_options + [
    resource_option(
        "--repository",
        default_plugin="rpm",
        default_type="rpm",
        context_table={"rpm:rpm": PulpRpmRepositoryContext},
        needs_plugins=[PluginRequirement("core", min="3.20.0")],
    )
]
publication.add_command(list_command(decorators=filter_options))
publication.add_command(show_command(decorators=lookup_options))
publication.add_command(create_command(decorators=create_options))
publication.add_command(destroy_command(decorators=lookup_options))
