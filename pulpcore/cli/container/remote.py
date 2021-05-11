import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    common_remote_create_options,
    common_remote_update_options,
    create_command,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    load_json_callback,
    name_option,
    show_command,
    update_command,
)
from pulpcore.cli.container.context import PulpContainerRemoteContext

_ = gettext.gettext


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


lookup_options = [href_option, name_option]
remote_options = [
    click.option(
        "--policy", type=click.Choice(["immediate", "on_demand", "streamed"], case_sensitive=False)
    ),
    click.option("--include-tags", callback=load_json_callback),
    click.option("--exclude-tags", callback=load_json_callback),
]
remote_create_options = (
    common_remote_create_options + remote_options + [click.option("--upstream-name", required=True)]
)
remote_update_options = (
    lookup_options
    + common_remote_update_options
    + remote_options
    + [click.option("--upstream-name")]
)

remote.add_command(list_command(decorators=[label_select_option]))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(create_command(decorators=remote_create_options))
remote.add_command(update_command(decorators=remote_update_options))
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(label_command())
