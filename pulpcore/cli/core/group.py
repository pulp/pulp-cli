import click

from pulpcore.cli.common.generic import (
    list_entities,
    show_by_name,
    destroy_by_name,
)
from pulpcore.cli.common.context import (
    pass_pulp_context,
    pass_entity_context,
    PulpContext,
    PulpEntityContext,
)
from pulpcore.cli.core.context import (
    PulpGroupContext,
)


@click.group()
@pass_pulp_context
@click.pass_context
def group(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpGroupContext(pulp_ctx)


group.add_command(list_entities)
group.add_command(show_by_name)


@group.command()
@click.option("--name", required=True)
@pass_entity_context
@pass_pulp_context
def create(pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, name: str) -> None:
    entity = {"name": name}
    result = entity_ctx.create(body=entity)
    pulp_ctx.output_result(result)


group.add_command(destroy_by_name)
