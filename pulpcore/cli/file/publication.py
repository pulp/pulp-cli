import click
from pulp_glue.common.context import PluginRequirement
from pulp_glue.common.i18n import get_translation
from pulp_glue.file.context import (
    PulpFilePublicationContext,
    PulpFileRepositoryContext,
)

from pulp_cli.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    href_option,
    list_command,
    pass_pulp_context,
    publication_filter_options,
    pulp_group,
    pulp_option,
    resource_option,
    role_command,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="file",
    default_type="file",
    context_table={"file:file": PulpFileRepositoryContext},
    href_pattern=PulpFileRepositoryContext.HREF_PATTERN,
)


@pulp_group()
@click.option(
    "-t",
    "--type",
    "publication_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@pass_pulp_context
@click.pass_context
def publication(ctx: click.Context, pulp_ctx: PulpCLIContext, /, publication_type: str) -> None:
    if publication_type == "file":
        ctx.obj = PulpFilePublicationContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option]
create_options = [
    repository_option,
    click.option(
        "--version", type=int, help=_("a repository version number, leave blank for latest")
    ),
    click.option(
        "--manifest",
        help=_("Filename to use for manifest file containing metadata for all the files."),
    ),
    pulp_option(
        "--checkpoint",
        is_flag=True,
        default=None,
        help=_("Create a checkpoint publication"),
        needs_plugins=[PluginRequirement("core", specifier=">=3.74.0")],
    ),
]
publication.add_command(list_command(decorators=publication_filter_options + [repository_option]))
publication.add_command(show_command(decorators=lookup_options))
publication.add_command(create_command(decorators=create_options))
publication.add_command(destroy_command(decorators=lookup_options))
publication.add_command(role_command(decorators=lookup_options))
