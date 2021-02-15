import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import href_option, list_command, show_command
from pulpcore.cli.migration.context import (
    PulpMigrationPulp2ContentContext,
    PulpMigrationPulp2RepositoryContext,
)


@click.group()
def pulp2() -> None:
    pass


@pulp2.group()
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpMigrationPulp2ContentContext(pulp_ctx)


content.add_command(list_command())
content.add_command(show_command(decorators=[href_option]))


@pulp2.group()
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpMigrationPulp2RepositoryContext(pulp_ctx)
    pass


repository.add_command(list_command())
repository.add_command(show_command(decorators=[href_option]))
