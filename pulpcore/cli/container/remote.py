import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.container.context import PulpContainerRemoteContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    common_remote_create_options,
    common_remote_update_options,
    create_command,
    destroy_command,
    href_option,
    label_command,
    list_command,
    load_json_callback,
    name_option,
    pass_pulp_context,
    pulp_group,
    remote_filter_options,
    remote_lookup_option,
    role_command,
    show_command,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@click.option(
    "-t",
    "--type",
    "remote_type",
    type=click.Choice(["container"], case_sensitive=False),
    default="container",
)
@pass_pulp_context
@click.pass_context
def remote(ctx: click.Context, pulp_ctx: PulpCLIContext, remote_type: str) -> None:
    if remote_type == "container":
        ctx.obj = PulpContainerRemoteContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option, remote_lookup_option]
nested_lookup_options = [remote_lookup_option]
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

remote.add_command(list_command(decorators=remote_filter_options))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(create_command(decorators=remote_create_options))
remote.add_command(update_command(decorators=remote_update_options))
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(role_command(decorators=lookup_options))
remote.add_command(label_command(decorators=nested_lookup_options))
