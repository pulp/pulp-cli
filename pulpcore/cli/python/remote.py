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
from pulpcore.cli.python.context import PulpPythonRemoteContext

_ = gettext.gettext


@click.group()
@click.option(
    "-t",
    "--type",
    "remote_type",
    type=click.Choice(["python"], case_sensitive=False),
    default="python",
)
@pass_pulp_context
@click.pass_context
def remote(ctx: click.Context, pulp_ctx: PulpContext, remote_type: str) -> None:
    if remote_type == "python":
        ctx.obj = PulpPythonRemoteContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option]
python_remote_options = [
    click.option("--includes", callback=load_json_callback, help=_("Package allowlist")),
    click.option("--excludes", callback=load_json_callback, help=_("Package blocklist")),
    click.option("--prereleases", type=click.BOOL, default=True),
    click.option("--keep-latest-packages", type=int),
    click.option("--package-types", callback=load_json_callback),
    click.option("--exclude-platforms", callback=load_json_callback),
]
remote.add_command(list_command(decorators=[label_select_option]))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(create_command(decorators=common_remote_create_options + python_remote_options))
remote.add_command(
    update_command(decorators=lookup_options + common_remote_update_options + python_remote_options)
)
remote.add_command(label_command())

# TODO Add support for 'from_bandersnatch' remote create endpoint
