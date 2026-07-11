import click

from pulp_glue.common.i18n import get_translation
from pulp_glue.hugging_face.context import PulpHuggingFaceRemoteContext

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
    remote_filter_options,
    remote_lookup_option,
    show_command,
    type_option,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@type_option(choices={"hugging-face": PulpHuggingFaceRemoteContext})
def remote() -> None:
    pass


lookup_options = [href_option, name_option, remote_lookup_option]
nested_lookup_options = [remote_lookup_option]
hugging_face_remote_options = [
    click.option(
        "--hf-token",
        "hf_token",
        help=_(
            "Hugging Face API token for accessing private repositories."
            " WARNING: the plugin stores this token and returns it in API responses;"
            " prefer a scoped, read-only token."
        ),
    ),
    click.option(
        "--policy",
        type=click.Choice(["immediate", "on_demand", "streamed"], case_sensitive=False),
        help=_("Policy for downloading content (use 'on_demand' for pull-through caching)."),
    ),
]

remote.add_command(list_command(decorators=remote_filter_options))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(
    create_command(decorators=common_remote_create_options + hugging_face_remote_options)
)
remote.add_command(
    update_command(
        decorators=lookup_options + common_remote_update_options + hugging_face_remote_options
    )
)
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(label_command(decorators=nested_lookup_options))
