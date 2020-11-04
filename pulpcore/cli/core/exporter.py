from pulpcore.cli.common import (
    DEFAULT_LIMIT,
    PulpContext,
    PulpEntityContext,
    RepositoryDefinition,
)

from typing import Any, List
import click


class ExporterContext(PulpEntityContext):
    ENTITY: str = "Exporter"


class PulpExporterContext(ExporterContext):
    ENTITY: str = "PulpExporter"
    HREF: str = "pulp_exporter_href"
    CREATE_ID: str = "exporters_core_pulp_create"
    READ_ID: str = "exporters_core_pulp_read"
    UPDATE_ID: str = "exporters_core_pulp_update"
    DELETE_ID: str = "exporters_core_pulp_delete"
    LIST_ID: str = "exporters_core_pulp_list"

    def delete(self, name: str) -> Any:
        the_exporter = self.find(name=name)
        return super().delete(the_exporter["pulp_href"])


@click.group()
@click.pass_context
def exporter(ctx: click.Context) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    ctx.obj = ExporterContext(pulp_ctx)


@exporter.group()
@click.pass_context
def pulp(ctx: click.Context) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    ctx.obj = PulpExporterContext(pulp_ctx)


@pulp.command()
@click.option("--name", required=True)
@click.option("--path", type=str, required=True)
@click.option("--repository", type=tuple([str, str]), multiple=True, required=True)
@click.pass_context
def create(
    ctx: click.Context, name: str, path: str, repository: List[RepositoryDefinition]
) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    pexporter_ctx: PulpExporterContext = ctx.find_object(PulpExporterContext)
    repo_hrefs = []
    for repo_tuple in repository:
        repo_hrefs.append(pexporter_ctx.find_repository(repo_tuple)["pulp_href"])

    params = {"name": name, "path": path, "repositories": repo_hrefs}
    result = pexporter_ctx.create(body=params)
    pulp_ctx.output_result(result)


@pulp.command()
@click.option("--name", required=True, help="Name of the PulpExporter")
@click.pass_context
def read(ctx: click.Context, name: str) -> None:
    """Shows details of an artifact."""
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    pexporter_ctx: PulpExporterContext = ctx.find_object(PulpExporterContext)
    the_exporter = pexporter_ctx.find(name=name)
    entity = pexporter_ctx.show(the_exporter["pulp_href"])
    pulp_ctx.output_result(entity)


@pulp.command()
@click.option("--name", required=True)
@click.option("--path")
@click.option("--repository", type=tuple([str, str]), multiple=True)
@click.pass_context
def update(
    ctx: click.Context, name: str, path: str, repository: List[RepositoryDefinition]
) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    pexporter_ctx: PulpExporterContext = ctx.find_object(PulpExporterContext)
    the_exporter = pexporter_ctx.find(name=name)
    exporter_href = the_exporter["pulp_href"]

    if path:
        the_exporter["path"] = path

    if repository:
        repo_hrefs = []
        for repo_tuple in repository:
            repo_hrefs.append(pexporter_ctx.find_repository(repo_tuple)["pulp_href"])
        the_exporter["repositories"] = repo_hrefs

    result = pexporter_ctx.update(exporter_href, the_exporter)
    pulp_ctx.output_result(result)


@pulp.command()
@click.option("--name", required=True)
@click.pass_context
def delete(ctx: click.Context, name: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    pexporter_ctx: PulpExporterContext = ctx.find_object(PulpExporterContext)
    result = pexporter_ctx.delete(name)
    pulp_ctx.output_result(result)


@pulp.command()
@click.option("--name", type=str)
@click.option(
    "--limit", default=DEFAULT_LIMIT, type=int, help="Limit the number of exporters to show."
)
@click.option("--offset", default=0, type=int, help="Skip a number of exporters to show.")
@click.pass_context
def list(ctx: click.Context, limit: int, offset: int, **kwargs: Any) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    pexporter_ctx: PulpExporterContext = ctx.find_object(PulpExporterContext)
    params = {k: v for k, v in kwargs.items() if v is not None}
    result = pexporter_ctx.list(limit=limit, offset=offset, parameters=params)
    pulp_ctx.output_result(result)
