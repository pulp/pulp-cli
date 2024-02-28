import gettext
import typing as t

import click
from pulp_glue.common.context import EntityFieldDefinition, PulpEntityContext
from pulp_glue.rpm.context import PulpRpmCompsXmlContext, PulpRpmRepositoryContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    pass_pulp_context,
    pulp_command,
    resource_option,
)

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
    pulp_ctx: PulpCLIContext,
    file: t.IO[bytes],
    repository: t.Optional[EntityFieldDefinition],
    replace: t.Optional[bool],
) -> None:
    """Create comps.xml content-units by uploading a comps.xml-formatted file"""
    entity_ctx = PulpRpmCompsXmlContext(pulp_ctx)
    href = None
    if isinstance(repository, PulpEntityContext):
        href = repository.pulp_href
    result = entity_ctx.upload_comps(file, href, replace)
    pulp_ctx.output_result(result)
