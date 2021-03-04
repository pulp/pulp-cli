import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    show_command,
    update_command,
)
from pulpcore.cli.file.context import PulpFileRemoteContext

_ = gettext.gettext


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
create_options = [
    click.option("--name", required=True),
    click.option("--url", required=True),
    click.option("--ca-cert"),
    click.option("--client-cert"),
    click.option("--client-key"),
    click.option("--connect-timeout", type=float),
    click.option("--download-concurrency", type=int),
    click.option("--password"),
    click.option(
        "--policy", type=click.Choice(["immediate", "on_demand", "streamed"], case_sensitive=False)
    ),
    click.option("--proxy-url"),
    click.option("--proxy-username"),
    click.option("--proxy-password"),
    click.option("--sock-connect-timeout", type=float),
    click.option("--sock-read-timeout", type=float),
    click.option("--tls-validation", type=bool),
    click.option("--total-timeout", type=float),
    click.option("--username"),
]
update_options = [
    click.option("--url"),
    click.option("--ca-cert"),
    click.option("--client-cert"),
    click.option("--client-key"),
    click.option("--connect-timeout", type=float),
    click.option("--download-concurrency", type=int),
    click.option("--password"),
    click.option(
        "--policy", type=click.Choice(["immediate", "on_demand", "streamed"], case_sensitive=False)
    ),
    click.option("--proxy-url"),
    click.option("--proxy-username"),
    click.option("--proxy-password"),
    click.option("--sock-connect-timeout", type=float),
    click.option("--sock-read-timeout", type=float),
    click.option("--tls-validation", type=bool),
    click.option("--total-timeout", type=float),
    click.option("--username"),
]

remote.add_command(list_command(decorators=[label_select_option]))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(create_command(decorators=create_options))
remote.add_command(update_command(decorators=lookup_options + update_options))
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(label_command())
