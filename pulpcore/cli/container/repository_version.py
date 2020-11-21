import click

from pulpcore.cli.common.generic import (
    list_entities,
    show_version,
    destroy_version,
)
from pulpcore.cli.common.context import (
    pass_pulp_context,
    pass_repository_context,
    PulpContext,
    PulpRepositoryContext,
)


@click.group()
@click.option("--repository", required=True)
@pass_repository_context
@pass_pulp_context
@click.pass_context
def version(
    ctx: click.Context,
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    repository: str,
) -> None:
    ctx.obj = repository_ctx.VERSION_CONTEXT(pulp_ctx)
    ctx.obj.repository = repository_ctx.find(name=repository)


version.add_command(list_entities)
version.add_command(show_version)
version.add_command(destroy_version)
