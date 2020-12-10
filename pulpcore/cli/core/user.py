import click

from pulpcore.cli.common.generic import (
    list_entities,
)
from pulpcore.cli.common.context import (
    pass_pulp_context,
    pass_entity_context,
    PulpContext,
    PulpEntityContext,
)
from pulpcore.cli.core.context import (
    PulpUserContext,
)


@click.group()
@pass_pulp_context
@click.pass_context
def user(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpUserContext(pulp_ctx)


user.add_command(list_entities)


@user.command()
@click.option("--username", required=True, help="Username of the entry")
@pass_entity_context
@pass_pulp_context
def show(pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, username: str) -> None:
    """Shows details of an entry"""
    href = entity_ctx.find(username=username)["pulp_href"]
    entity = entity_ctx.show(href)
    pulp_ctx.output_result(entity)
