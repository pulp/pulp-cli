import click
from pulp_glue.common.context import PluginRequirement
from pulp_glue.common.i18n import get_translation
from pulp_glue.rpm.context import PulpRpmPublicationContext, PulpRpmRepositoryContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    href_option,
    list_command,
    load_json_callback,
    pass_pulp_context,
    publication_filter_options,
    pulp_group,
    pulp_option,
    resource_option,
    role_command,
    show_command,
)
from pulpcore.cli.rpm.common import CHECKSUM_CHOICES

translation = get_translation(__package__)
_ = translation.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="rpm",
    default_type="rpm",
    context_table={"rpm:rpm": PulpRpmRepositoryContext},
    href_pattern=PulpRpmRepositoryContext.HREF_PATTERN,
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
def publication(ctx: click.Context, pulp_ctx: PulpCLIContext, publication_type: str) -> None:
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
    pulp_option(
        "--repo-config",
        "repo_config",
        needs_plugins=[PluginRequirement("rpm", specifier=">=3.24.0")],
        help=_(
            "A JSON dictionary describing config.repo file (or "
            "@file containing a JSON dictionary)"
        ),
        callback=load_json_callback,
    ),
    pulp_option(
        "--checksum-type",
        type=click.Choice(CHECKSUM_CHOICES, case_sensitive=False),
        help=_(
            "Option specifying the checksum type to use for package and metadata integrity checks."
        ),
        needs_plugins=[PluginRequirement("rpm", specifier=">=3.25.0")],
    ),
]
publication.add_command(list_command(decorators=publication_filter_options + [repository_option]))
publication.add_command(show_command(decorators=lookup_options))
publication.add_command(create_command(decorators=create_options))
publication.add_command(destroy_command(decorators=lookup_options))
publication.add_command(role_command(decorators=lookup_options))
