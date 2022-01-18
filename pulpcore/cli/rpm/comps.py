import gettext
from typing import IO, Optional

import click

from pulpcore.cli.common.context import (
    EntityFieldDefinition,
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import pulp_command, resource_option
from pulpcore.cli.rpm.context import PulpRpmCompsXmlContext, PulpRpmRepositoryContext

_ = gettext.gettext

repository_option = resource_option(
    "--repository",
    default_plugin="rpm",
    default_type="rpm",
    context_table={"rpm:rpm": PulpRpmRepositoryContext},
    href_pattern=PulpRpmRepositoryContext.HREF_PATTERN,
    help=_("Repository to associate the comps-units to, takes <name> or href."),
)


@pulp_command()
@click.option("--file", type=click.File("rb"), required=True)
@repository_option
@click.option("--replace", type=bool, default=False)
@pass_pulp_context
def comps_upload(
    pulp_ctx: PulpContext,
    file: IO[bytes],
    repository: Optional[EntityFieldDefinition],
    replace: Optional[bool],
) -> None:
    """Create comps.xml content-units by uploading a comps.xml-formatted file"""
    pulp_ctx.needs_plugin(PluginRequirement("rpm", min="3.17.0dev"))
    entity_ctx = PulpRpmCompsXmlContext(pulp_ctx)
    href = None
    if isinstance(repository, PulpEntityContext):
        href = repository.pulp_href
    result = entity_ctx.upload_comps(file, href, replace)
    pulp_ctx.output_result(result)
