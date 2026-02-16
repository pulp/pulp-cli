import click

from pulp_glue.common.i18n import get_translation
from pulp_glue.file.context import PulpFileGitRemoteContext, PulpFileRemoteContext

from pulp_cli.generic import (
    common_remote_create_options,
    common_remote_update_options,
    create_command,
    destroy_command,
    href_option,
    label_command,
    list_command,
    name_option,
    pulp_group,
    pulp_option,
    remote_filter_options,
    remote_lookup_option,
    role_command,
    show_command,
    type_option,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@type_option(choices={"file": PulpFileRemoteContext, "git": PulpFileGitRemoteContext})
def remote() -> None:
    pass


lookup_options = [href_option, name_option, remote_lookup_option]
nested_lookup_options = [remote_lookup_option]
file_remote_options = [
    pulp_option(
        "--policy",
        type=click.Choice(["immediate", "on_demand", "streamed"], case_sensitive=False),
        allowed_with_contexts=(PulpFileRemoteContext,),
    ),
    pulp_option(
        "--git-ref",
        help=_("The git ref (branch, tag, or commit hash) to sync from. Defaults to HEAD."),
        allowed_with_contexts=(PulpFileGitRemoteContext,),
    ),
]

remote.add_command(list_command(decorators=remote_filter_options))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(create_command(decorators=common_remote_create_options + file_remote_options))
remote.add_command(
    update_command(decorators=lookup_options + common_remote_update_options + file_remote_options)
)
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(label_command(decorators=nested_lookup_options))
remote.add_command(role_command(decorators=lookup_options))
