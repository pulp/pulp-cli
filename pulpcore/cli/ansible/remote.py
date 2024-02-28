import typing as t

import click
import yaml
from pulp_glue.ansible.context import (
    PulpAnsibleCollectionRemoteContext,
    PulpAnsibleRoleRemoteContext,
)
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    common_remote_create_options,
    common_remote_update_options,
    create_command,
    destroy_command,
    href_option,
    label_command,
    list_command,
    load_file_wrapper,
    name_option,
    pass_pulp_context,
    pulp_group,
    pulp_option,
    remote_filter_options,
    remote_lookup_option,
    show_command,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


def yaml_callback(
    ctx: click.Context, param: click.Parameter, value: t.Any
) -> t.Optional[t.Union[str, t.Any]]:
    if value:
        return f"{yaml.safe_load(value)}"
    return value


load_yaml_callback = load_file_wrapper(yaml_callback)


@pulp_group()
@click.option(
    "-t",
    "--type",
    "remote_type",
    type=click.Choice(["collection", "role"], case_sensitive=False),
    default="collection",
    is_eager=True,
)
@pass_pulp_context
@click.pass_context
def remote(ctx: click.Context, pulp_ctx: PulpCLIContext, remote_type: str) -> None:
    if remote_type == "role":
        ctx.obj = PulpAnsibleRoleRemoteContext(pulp_ctx)
    elif remote_type == "collection":
        ctx.obj = PulpAnsibleCollectionRemoteContext(pulp_ctx)
    else:
        raise NotImplementedError()


collection_context = (PulpAnsibleCollectionRemoteContext,)
lookup_options = [href_option, name_option, remote_lookup_option]
nested_lookup_options = [remote_lookup_option]
remote_options = [
    click.option("--policy", help=_("policy to use when downloading")),
]
collection_options = [
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
ansible_remote_options = remote_options + collection_options
create_options = common_remote_create_options + remote_options + ansible_remote_options
update_options = common_remote_update_options + remote_options + ansible_remote_options

remote.add_command(list_command(decorators=remote_filter_options))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(create_command(decorators=create_options))
remote.add_command(update_command(decorators=lookup_options + update_options))
remote.add_command(label_command(decorators=nested_lookup_options))
