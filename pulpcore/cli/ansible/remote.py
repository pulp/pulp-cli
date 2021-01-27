from typing import Any, Dict, Optional

import click
import yaml

from pulpcore.cli.ansible.context import (
    PulpAnsibleCollectionRemoteContext,
    PulpAnsibleRoleRemoteContext,
)
from pulpcore.cli.common.context import (
    EntityDefinition,
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import destroy_by_name, list_entities, show_by_name


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


remote_options = {
    "ca-cert": (str, "a PEM encoded CA certificate"),
    "client-cert": (str, "a PEM encoded client certificate"),
    "client-key": (str, "a PEM encode private key"),
    "tls-validation": (str, "if True, TLS peer validation must be performed"),
    "proxy-url": (str, "format: scheme//user:password@host:port"),
    "username": (str, "used for authentication when syncing"),
    "password": (str, ""),
    "download-concurrency": (int, "total number of simultaneous connections"),
    "policy": (str, "policy to use when downloading"),
    "total-timeout": (str, "aiohttp.ClientTimeout.total for download connections"),
    "connect-timeout": (str, "aiohttp.ClientTimeout.connect for download connections"),
    "sock-connect-timeout": (str, "aiohttp.ClientTimeout.sock_connect for download connections"),
    "sock-read-timeout": (str, "aiohttp.ClientTimeout.sock_read for download connections"),
}


def check_collection_options(
    remote_ctx: PulpEntityContext,
    requirements_file: Any,
    requirements: Optional[str],
    auth_url: Optional[str],
    token: Optional[str],
) -> EntityDefinition:

    body: EntityDefinition = dict()
    if isinstance(remote_ctx, PulpAnsibleRoleRemoteContext) and any(
        [requirements_file, requirements, auth_url, token]
    ):
        raise click.ClickException("Options not valid for Role remote, see --help")
    if requirements_file is not None:
        body["requirements_file"] = f"{yaml.safe_load(requirements_file)}"
    elif requirements is not None:
        body["requirements_file"] = yaml.safe_load(f'"{requirements}"')
    if auth_url is not None:
        body["auth_url"] = auth_url
    if token is not None:
        body["token"] = token
    return body


remote.add_command(list_entities)
remote.add_command(show_by_name)
remote.add_command(destroy_by_name)


@remote.command(name="create")
@click.option("--name", required=True)
@click.option("--url", required=True)
@click.option(
    "--requirements-file",
    type=click.File(),
    help="Collections only: a Collection requirements yaml",
)
@click.option("--requirements", help="Collections only: a string of a requirements yaml")
@click.option("--auth-url", help="Collections only: URL to receive a session token")
@click.option("--token", help="Collections only: token key use for authentication")
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    remote_ctx: PulpEntityContext,
    name: str,
    url: str,
    requirements_file: Any,
    requirements: Optional[str],
    auth_url: Optional[str],
    token: Optional[str],
    **remote_options: Dict[str, Any],
) -> None:
    """
    Creates a Collection or Role remote based on -t parameter

    e.g. pulp ansible remote -t role create ...
    """
    body: EntityDefinition = {"name": name, "url": url}

    body.update(
        check_collection_options(
            remote_ctx=remote_ctx,
            requirements_file=requirements_file,
            requirements=requirements,
            auth_url=auth_url,
            token=token,
        )
    )

    if remote_options:
        removed_nulls = {k: v for k, v in remote_options.items() if v is not None}
        body.update(removed_nulls)
    result = remote_ctx.create(body=body)
    pulp_ctx.output_result(result)


@remote.command(name="update")
@click.option("--name", required=True)
@click.option("--url")
@click.option(
    "--requirements-file", type=click.File(), help="Collections only: new requirements yaml file"
)
@click.option("--requirements", help="Collections only: new yaml string of requirements")
@click.option("--auth-url", help="Collections only: new authentication url")
@click.option("--token", help="Collections only: new token for authentication")
@pass_entity_context
@pass_pulp_context
def update(
    pulp_ctx: PulpContext,
    remote_ctx: PulpEntityContext,
    name: str,
    url: Optional[str],
    requirements_file: Any,
    requirements: Optional[str],
    auth_url: Optional[str],
    token: Optional[str],
    **remote_options: Dict[str, Any],
) -> None:
    """
    Use -t to specify the type of the remote you are updating

    e.g. pulp ansible remote -t role update ...
    """
    body: EntityDefinition = dict()

    body.update(
        check_collection_options(
            remote_ctx=remote_ctx,
            requirements_file=requirements_file,
            requirements=requirements,
            auth_url=auth_url,
            token=token,
        )
    )
    if url:
        body["url"] = url
    if remote_options:
        removed_nulls = {k: v for k, v in remote_options.items() if v is not None}
        body.update(removed_nulls)

    remote = remote_ctx.find(name=name)
    remote_href = remote["pulp_href"]
    remote_ctx.update(remote_href, body=body)
    result = remote_ctx.show(remote_href)
    pulp_ctx.output_result(result)


for k, v in remote_options.items():
    click.option(f"--{k}", type=v[0], help=v[1])(create)
    click.option(f"--{k}", type=v[0], help=v[1])(update)
