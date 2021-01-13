import click

from pulpcore.cli.common.context import PulpContext, pass_entity_context, pass_pulp_context
from pulpcore.cli.common.generic import (
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    show_command,
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

remote.add_command(list_command(decorators=[label_select_option]))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(label_command())


@remote.command()
@click.option("--name", required=True)
@click.option("--url", required=True)
@pass_entity_context
@pass_pulp_context
def create(pulp_ctx: PulpContext, remote_ctx: PulpFileRemoteContext, name: str, url: str) -> None:
    remote = {"name": name, "url": url}
    result = remote_ctx.create(body=remote)
    pulp_ctx.output_result(result)
