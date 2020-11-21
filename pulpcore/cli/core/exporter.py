from pulpcore.cli.common.context import (
    DEFAULT_LIMIT,
    pass_pulp_context,
    pass_entity_context,
    PulpContext,
    RepositoryDefinition,
)
from pulpcore.cli.core.context import (
    PulpExporterContext,
)

from typing import Any, List
import click


@click.group()
def exporter() -> None:
    pass


@exporter.group()
@pass_pulp_context
@click.pass_context
def pulp(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpExporterContext(pulp_ctx)


@pulp.command()
@click.option("--name", required=True)
@click.option("--path", type=str, required=True)
@click.option("--repository", type=tuple([str, str]), multiple=True, required=True)
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    exporter_ctx: PulpExporterContext,
    name: str,
    path: str,
    repository: List[RepositoryDefinition],
) -> None:
    repo_hrefs = []
    for repo_tuple in repository:
        repo_hrefs.append(exporter_ctx.find_repository(repo_tuple)["pulp_href"])

    params = {"name": name, "path": path, "repositories": repo_hrefs}
    result = exporter_ctx.create(body=params)
    pulp_ctx.output_result(result)


@pulp.command()
@click.option("--name", required=True, help="Name of the PulpExporter")
@pass_entity_context
@pass_pulp_context
def read(pulp_ctx: PulpContext, exporter_ctx: PulpExporterContext, name: str) -> None:
    """Shows details of an artifact."""
    the_exporter = exporter_ctx.find(name=name)
    entity = exporter_ctx.show(the_exporter["pulp_href"])
    pulp_ctx.output_result(entity)


@pulp.command()
@click.option("--name", required=True)
@click.option("--path")
@click.option("--repository", type=tuple([str, str]), multiple=True)
@pass_entity_context
@pass_pulp_context
def update(
    pulp_ctx: PulpContext,
    exporter_ctx: PulpExporterContext,
    name: str,
    path: str,
    repository: List[RepositoryDefinition],
) -> None:
    the_exporter = exporter_ctx.find(name=name)
    exporter_href = the_exporter["pulp_href"]

    if path:
        the_exporter["path"] = path

    if repository:
        repo_hrefs = []
        for repo_tuple in repository:
            repo_hrefs.append(exporter_ctx.find_repository(repo_tuple)["pulp_href"])
        the_exporter["repositories"] = repo_hrefs

    result = exporter_ctx.update(exporter_href, the_exporter)
    pulp_ctx.output_result(result)


@pulp.command()
@click.option("--name", required=True)
@pass_entity_context
@pass_pulp_context
def delete(pulp_ctx: PulpContext, exporter_ctx: PulpExporterContext, name: str) -> None:
    result = exporter_ctx.delete(name)
    pulp_ctx.output_result(result)


@pulp.command()
@click.option("--name", type=str)
@click.option(
    "--limit", default=DEFAULT_LIMIT, type=int, help="Limit the number of exporters to show."
)
@click.option("--offset", default=0, type=int, help="Skip a number of exporters to show.")
@pass_entity_context
@pass_pulp_context
def list(
    pulp_ctx: PulpContext, exporter_ctx: PulpExporterContext, limit: int, offset: int, **kwargs: Any
) -> None:
    params = {k: v for k, v in kwargs.items() if v is not None}
    result = exporter_ctx.list(limit=limit, offset=offset, parameters=params)
    pulp_ctx.output_result(result)
