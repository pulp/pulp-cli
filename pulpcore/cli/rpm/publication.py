from typing import Optional, Union

import click

from pulpcore.cli.common.context import (
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import destroy_command, href_option, list_command, show_command
from pulpcore.cli.rpm.context import PulpRpmPublicationContext, PulpRpmRepositoryContext


def _repository_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[Union[str, PulpEntityContext]]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx: PulpContext = ctx.find_object(PulpContext)
        return PulpRpmRepositoryContext(pulp_ctx, entity={"name": value})
    return value


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


@publication.command()
@click.option("--repository", required=True)
@click.option("--version", type=int, help="a repository version number, leave blank for latest")
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    publication_ctx: PulpRpmPublicationContext,
    repository: str,
    version: Optional[int],
) -> None:
    repository_href: str = PulpRpmRepositoryContext(pulp_ctx).find(name=repository)["pulp_href"]
    if version is not None:
        body = {"repository_version": f"{repository_href}versions/{version}/"}
    else:
        body = {"repository": repository_href}
    result = publication_ctx.create(body=body)
    publication = publication_ctx.show(result["created_resources"][0])
    pulp_ctx.output_result(publication)


lookup_options = [href_option]
publication.add_command(list_command())
publication.add_command(show_command(decorators=lookup_options))
publication.add_command(destroy_command(decorators=lookup_options))
