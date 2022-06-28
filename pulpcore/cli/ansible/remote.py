from typing import Any, Optional, Union

import click
import yaml

from pulpcore.cli.ansible.context import (
    PulpAnsibleCollectionRemoteContext,
    PulpAnsibleRoleRemoteContext,
)
from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import (
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
    show_command,
    update_command,
)
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


def _requirements_callback(
    ctx: click.Context, param: click.Parameter, value: Any
) -> Optional[Union[str, Any]]:
    if value:
        if param.name == "requirements_file":
            return f"{yaml.safe_load(value)}"
        elif param.name == "requirements":
            return yaml.safe_load(f'"{value}"')
    return value


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
def remote(ctx: click.Context, pulp_ctx: PulpContext, remote_type: str) -> None:
    if remote_type == "role":
        ctx.obj = PulpAnsibleRoleRemoteContext(pulp_ctx)
    elif remote_type == "collection":
        ctx.obj = PulpAnsibleCollectionRemoteContext(pulp_ctx)
    else:
        raise NotImplementedError()


collection_context = (PulpAnsibleCollectionRemoteContext,)
lookup_options = [href_option, name_option]
remote_options = [
    click.option("--policy", help=_("policy to use when downloading")),
]
collection_options = [
    pulp_option(
        "--requirements-file",
        callback=_requirements_callback,
        type=click.File(),
        help=_("Collections only: a Collection requirements yaml"),
        allowed_with_contexts=collection_context,
    ),
    pulp_option(
        "--requirements",
        callback=_requirements_callback,
        help=_("Collections only: a string of a requirements yaml"),
        allowed_with_contexts=collection_context,
    ),
    pulp_option(
        "--auth-url",
        callback=_requirements_callback,
        help=_("Collections only: URL to receive a session token"),
        allowed_with_contexts=collection_context,
    ),
    pulp_option(
        "--token",
        callback=_requirements_callback,
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
remote.add_command(label_command())
