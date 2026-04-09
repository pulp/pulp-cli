import typing as t

import click
import yaml

from pulp_glue.ansible.context import (
    PulpAnsibleCollectionRemoteContext,
    PulpAnsibleRoleRemoteContext,
)
from pulp_glue.common.i18n import get_translation

from pulp_cli.generic import (
    common_remote_create_options,
    common_remote_update_options,
    create_command,
    destroy_command,
    href_option,
    label_command,
    list_command,
    load_file_wrapper,
    name_option,
    pulp_group,
    pulp_option,
    remote_filter_options,
    remote_lookup_option,
    show_command,
    type_option,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


def yaml_callback(ctx: click.Context, param: click.Parameter, value: t.Any) -> str | t.Any | None:
    if value:
        return f"{yaml.safe_load(value)}"
    return value


load_yaml_callback = load_file_wrapper(yaml_callback)


@pulp_group()
@type_option(
    choices={
        "collection": PulpAnsibleCollectionRemoteContext,
        "role": PulpAnsibleRoleRemoteContext,
    }
)
def remote() -> None:
    pass


collection_context = (PulpAnsibleCollectionRemoteContext,)
lookup_options = [href_option, name_option, remote_lookup_option]
nested_lookup_options = [remote_lookup_option]
remote_options = [
    click.option("--policy", help=_("policy to use when downloading")),
    pulp_option(
        "--requirements-file",
        callback=yaml_callback,
        type=click.File(),
        help=_(
            "(Deprecated) Please use '--requirements' instead\n\n"
            "Collections only: a Collection requirements yaml"
        ),
        allowed_with_contexts=collection_context,
    ),
    pulp_option(
        "--requirements",
        callback=load_yaml_callback,
        help=_("Collections only: a string of a requirements yaml"),
        allowed_with_contexts=collection_context,
    ),
    pulp_option(
        "--auth-url",
        help=_("Collections only: URL to receive a session token"),
        allowed_with_contexts=collection_context,
    ),
    pulp_option(
        "--token",
        help=_("Collections only: token key use for authentication"),
        allowed_with_contexts=collection_context,
    ),
]
create_options = common_remote_create_options + remote_options
update_options = common_remote_update_options + remote_options

remote.add_command(list_command(decorators=remote_filter_options))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(create_command(decorators=create_options))
remote.add_command(update_command(decorators=lookup_options + update_options))
remote.add_command(label_command(decorators=nested_lookup_options))
