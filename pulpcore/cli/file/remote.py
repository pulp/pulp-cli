import click

from pulpcore.cli.common.generic import (
    list_command,
    show_command,
    destroy_command,
    name_option,
    href_option,
)
from pulpcore.cli.common.context import (
    PulpContext,
    pass_pulp_context,
    pass_entity_context,
)
from pulpcore.cli.file.context import PulpFileRemoteContext


@click.group()
@click.option(
    "-t",
    "--type",
    "remote_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@pass_pulp_context
@click.pass_context
def remote(ctx: click.Context, pulp_ctx: PulpContext, remote_type: str) -> None:
    if remote_type == "file":
        ctx.obj = PulpFileRemoteContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option]

remote.add_command(list_command())
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(destroy_command(decorators=lookup_options))


@remote.command()
@click.option("--name", required=True)
@click.option("--url", required=True)
@pass_entity_context
@pass_pulp_context
def create(pulp_ctx: PulpContext, remote_ctx: PulpFileRemoteContext, name: str, url: str) -> None:
    remote = {"name": name, "url": url}
    result = remote_ctx.create(body=remote)
    pulp_ctx.output_result(result)
