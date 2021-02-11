import gettext
from typing import Any, Optional, Union

import click
import yaml

from pulpcore.cli.ansible.context import (
    PulpAnsibleCollectionRemoteContext,
    PulpAnsibleRoleRemoteContext,
)
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

_ = gettext.gettext


def _requirements_callback(
    ctx: click.Context, param: click.Parameter, value: Any
) -> Optional[Union[str, Any]]:
    if value:
        if isinstance(ctx.obj, PulpAnsibleRoleRemoteContext):
            raise click.ClickException(f"Option {param.name} not valid for Role remote, see --help")
        if param.name == "requirements-file":
            return f"{yaml.safe_load(value)}"
        elif param.name == "requirements":
            return yaml.safe_load(f'"{value}"')
    return value


@click.group()
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


lookup_options = [href_option, name_option]
remote_options = [
    click.option("--ca-cert", help=_("a PEM encoded CA certificate")),
    click.option("--client-cert", help=_("a PEM encoded client certificate")),
    click.option("--client-key", help=_("a PEM encode private key")),
    click.option("--tls-validation", help=_("if True, TLS peer validation must be performed")),
    click.option("--proxy-url", help=_("format: scheme//user:password@host:port")),
    click.option("--username", help=_("used for authentication when syncing")),
    click.option("--password"),
    click.option(
        "--download-concurrency", type=int, help=_("total number of simultaneous connections")
    ),
    click.option("--policy", help=_("policy to use when downloading")),
    click.option(
        "--total-timeout",
        type=float,
        help=_("aiohttp.ClientTimeout.total for download connections"),
    ),
    click.option(
        "--connect-timeout",
        type=float,
        help=_("aiohttp.ClientTimeout.connect for download connections"),
    ),
    click.option(
        "--sock-connect-timeout",
        type=float,
        help=_("aiohttp.ClientTimeout.sock_connect for download connections"),
    ),
    click.option(
        "--sock-read-timeout",
        type=float,
        help=_("aiohttp.ClientTimeout.sock_read for download connections"),
    ),
    click.option("--rate-limit", type=int, help=_("limit download rate in requests per second")),
]
collection_options = [
    click.option(
        "--requirements-file",
        callback=_requirements_callback,
        type=click.File(),
        help=_("Collections only: a Collection requirements yaml"),
    ),
    click.option(
        "--requirements",
        callback=_requirements_callback,
        help=_("Collections only: a string of a requirements yaml"),
    ),
    click.option(
        "--auth-url",
        callback=_requirements_callback,
        help=_("Collections only: URL to receive a session token"),
    ),
    click.option(
        "--token",
        callback=_requirements_callback,
        help=_("Collections only: token key use for authentication"),
    ),
]
ansible_remote_options = remote_options + collection_options
create_options = [
    click.option("--name", required=True),
    click.option("--url", required=True),
] + ansible_remote_options
update_options = (
    lookup_options + [click.option("--url", help=_("new url"))] + ansible_remote_options
)

remote.add_command(list_command(decorators=[label_select_option]))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(create_command(decorators=create_options))
remote.add_command(update_command(decorators=update_options))
remote.add_command(label_command())
