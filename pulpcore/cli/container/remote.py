import click

from pulpcore.cli.common import (
    show_by_name,
    destroy_by_name,
    limit_option,
    offset_option,
    PulpContext,
    PulpEntityContext,
)


class PulpContainerRemoteContext(PulpEntityContext):
    ENTITY: str = "remote"
    HREF: str = "container_container_remote_href"
    LIST_ID: str = "remotes_container_container_list"
    CREATE_ID: str = "remotes_container_container_create"
    UPDATE_ID: str = "remotes_container_container_update"
    DELETE_ID: str = "remotes_container_container_delete"


@click.group()
@click.option(
    "-t",
    "--type",
    "remote_type",
    type=click.Choice(["container"], case_sensitive=False),
    default="container",
)
@click.pass_context
def remote(ctx: click.Context, remote_type: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)

    if remote_type == "container":
        ctx.obj = PulpContainerRemoteContext(pulp_ctx)
    else:
        raise NotImplementedError()


@remote.command()
@limit_option
@offset_option
@click.pass_context
def list(ctx: click.Context, limit: int, offset: int) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    remote_ctx: PulpContainerRemoteContext = ctx.find_object(PulpContainerRemoteContext)

    result = remote_ctx.list(limit=limit, offset=offset, parameters={})
    pulp_ctx.output_result(result)


remote.add_command(show_by_name)


@remote.command()
@click.option("--name", required=True)
@click.option("--upstream-name", required=True)
@click.option("--url", required=True)
@click.pass_context
def create(ctx: click.Context, name: str, upstream_name: str, url: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    remote_ctx: PulpContainerRemoteContext = ctx.find_object(PulpContainerRemoteContext)

    remote = {"name": name, "upstream_name": upstream_name, "url": url}
    result = remote_ctx.create(body=remote)
    pulp_ctx.output_result(result)


remote.add_command(destroy_by_name)
