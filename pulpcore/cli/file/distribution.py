from typing import Optional

import click


from pulpcore.cli.common import (
    show_by_name,
    destroy_by_name,
    limit_option,
    offset_option,
    PulpContext,
    PulpEntityContext,
)


class PulpFileDistributionContext(PulpEntityContext):
    ENTITY: str = "distribution"
    HREF: str = "file_file_distribution_href"
    LIST_ID: str = "distributions_file_file_list"
    READ_ID: str = "distributions_file_file_read"
    CREATE_ID: str = "distributions_file_file_create"
    UPDATE_ID: str = "distributions_file_file_update"
    DELETE_ID: str = "distributions_file_file_delete"
    SYNC_ID: str = "distributions_file_file_sync"


@click.group()
@click.option(
    "-t",
    "--type",
    "distribution_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@click.pass_context
def distribution(ctx: click.Context, distribution_type: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)

    if distribution_type == "file":
        ctx.obj = PulpFileDistributionContext(pulp_ctx)
    else:
        raise NotImplementedError()


@distribution.command()
@limit_option
@offset_option
@click.pass_context
def list(ctx: click.Context, limit: int, offset: int) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    distribution_ctx: PulpFileDistributionContext = ctx.find_object(PulpFileDistributionContext)

    result = distribution_ctx.list(limit=limit, offset=offset, parameters={})
    pulp_ctx.output_result(result)


distribution.add_command(show_by_name)


@distribution.command()
@click.option("--name", required=True)
@click.option("--base-path", required=True)
@click.option("--publication")
@click.pass_context
def create(ctx: click.Context, name: str, base_path: str, publication: Optional[str]) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    distribution_ctx: PulpFileDistributionContext = ctx.find_object(PulpFileDistributionContext)

    body = {"name": name, "base_path": base_path}
    if publication:
        body["publication"] = publication
    result = distribution_ctx.create(body=body)
    distribution = distribution_ctx.show(result["created_resources"][0])
    pulp_ctx.output_result(distribution)


distribution.add_command(destroy_by_name)
