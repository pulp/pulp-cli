import click

from pulpcore.cli.common.context import PulpContext, pass_entity_context, pass_pulp_context
from pulpcore.cli.common.generic import destroy_by_name, list_entities, show_by_name
from pulpcore.cli.container.context import PulpContainerRemoteContext


@click.group()
@click.option(
    "-t",
    "--type",
    "remote_type",
    type=click.Choice(["container"], case_sensitive=False),
    default="container",
)
@pass_pulp_context
@click.pass_context
def remote(ctx: click.Context, pulp_ctx: PulpContext, remote_type: str) -> None:
    if remote_type == "container":
        ctx.obj = PulpContainerRemoteContext(pulp_ctx)
    else:
        raise NotImplementedError()


remote.add_command(list_entities)
remote.add_command(show_by_name)


@remote.command()
@click.option("--name", required=True)
@click.option("--upstream-name", required=True)
@click.option("--url", required=True)
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    remote_ctx: PulpContainerRemoteContext,
    name: str,
    upstream_name: str,
    url: str,
) -> None:
    remote = {"name": name, "upstream_name": upstream_name, "url": url}
    result = remote_ctx.create(body=remote)
    pulp_ctx.output_result(result)


remote.add_command(destroy_by_name)
