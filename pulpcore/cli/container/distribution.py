from typing import Optional

import click


from pulpcore.cli.common.generic import (
    list_entities,
    show_by_name,
    destroy_by_name,
)
from pulpcore.cli.common.context import (
    PulpContext,
    PulpRepositoryContext,
    pass_pulp_context,
    pass_entity_context,
)
from pulpcore.cli.container.context import (
    PulpContainerDistributionContext,
    PulpContainerRepositoryContext,
    PulpContainerPushRepositoryContext,
)


@click.group()
@click.option(
    "-t",
    "--type",
    "distribution_type",
    type=click.Choice(["container"], case_sensitive=False),
    default="container",
)
@pass_pulp_context
@click.pass_context
def distribution(ctx: click.Context, pulp_ctx: PulpContext, distribution_type: str) -> None:
    if distribution_type == "container":
        ctx.obj = PulpContainerDistributionContext(pulp_ctx)
    else:
        raise NotImplementedError()


distribution.add_command(list_entities)
distribution.add_command(show_by_name)


@distribution.command()
@click.option("--name", required=True)
@click.option("--base-path", required=True)
@click.option("--repository")
@click.option(
    "-t",
    "--repository-type",
    "repository_type",
    type=click.Choice(["container", "push"], case_sensitive=False),
    default="container",
)
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    distribution_ctx: PulpContainerDistributionContext,
    name: str,
    base_path: str,
    repository: Optional[str],
    repository_type: Optional[str],
) -> None:
    repository_ctx: PulpRepositoryContext
    body = {"name": name, "base_path": base_path}
    if repository:
        if repository_type == "container":
            repository_ctx = PulpContainerRepositoryContext(pulp_ctx)
        elif repository_type == "push":
            repository_ctx = PulpContainerPushRepositoryContext(pulp_ctx)
        else:
            raise NotImplementedError()
        repository_href = repository_ctx.find(name=repository)["pulp_href"]
        body["repository"] = repository_href
    result = distribution_ctx.create(body=body)
    distribution = distribution_ctx.show(result["created_resources"][0])
    pulp_ctx.output_result(distribution)


distribution.add_command(destroy_by_name)
