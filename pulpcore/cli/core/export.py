from pulpcore.cli.common import (
    DEFAULT_LIMIT,
    PulpContext,
    PulpEntityContext,
    RepositoryVersionDefinition,
)

from typing import Any, Dict, List
import click


class PulpExportContext(PulpEntityContext):
    ENTITY: str = "PulpExport"
    HREF: str = "core_pulp_pulp_export_href"
    READ_ID: str = "exporters_core_pulp_exports_read"
    DELETE_ID: str = "exporters_core_pulp_exports_delete"
    LIST_ID: str = "exporters_core_pulp_exports_list"
    EXPORTER_LIST_ID: str = "exporters_core_pulp_list"
    CREATE_ID: str = "exporters_core_pulp_exports_create"

    def find_exporter(self, name: str) -> Any:
        search_result = self.pulp_ctx.call(
            self.EXPORTER_LIST_ID, parameters={"name": name, "limit": 1}
        )
        if search_result["count"] != 1:
            raise click.ClickException(f"PulpExporter '{name}' not found.")
        exporter = search_result["results"][0]
        return exporter


@click.group()
@click.pass_context
def export(ctx: click.Context) -> None:
    pass


@export.group()
@click.pass_context
def pulp(ctx: click.Context) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    ctx.obj = PulpExportContext(pulp_ctx)


@pulp.command()
@click.option("--href", required=True, help="HREF of the PulpExport")
@click.pass_context
def read(ctx: click.Context, href: str) -> None:
    """Shows details of an artifact."""
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    export_ctx: PulpExportContext = ctx.find_object(PulpExportContext)

    entity = export_ctx.show(href)
    pulp_ctx.output_result(entity)


@pulp.command()
@click.option("--href", required=True)
@click.pass_context
def delete(ctx: click.Context, href: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    pexporter_ctx: PulpExportContext = ctx.find_object(PulpExportContext)
    result = pexporter_ctx.delete(href)
    pulp_ctx.output_result(result)


@pulp.command()
@click.option("--exporter", type=str, required=True, help="Name of owning PulpExporter")
@click.option(
    "--limit", default=DEFAULT_LIMIT, type=int, help="Limit the number of exporters to show."
)
@click.option("--offset", default=0, type=int, help="Skip a number of exporters to show.")
@click.pass_context
def list(ctx: click.Context, exporter: str, limit: int, offset: int, **kwargs: Any) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    pexport_ctx: PulpExportContext = ctx.find_object(PulpExportContext)
    params = {k: v for k, v in kwargs.items() if v is not None}
    the_exporter = pexport_ctx.find_exporter(exporter)
    params["pulp_exporter_href"] = the_exporter["pulp_href"]
    result = pexport_ctx.list(limit=limit, offset=offset, parameters=params)
    pulp_ctx.output_result(result)


@pulp.command()
@click.option("--exporter", required=True)
@click.option("--full", type=bool, default=True)
@click.option("--chunk-size", type=str, help="Examples: 512MB, 1GB")
@click.option("--versions", type=tuple([str, str, int]), multiple=True)
@click.option("--start-versions", type=tuple([str, str, int]), multiple=True)
@click.pass_context
def run(
    ctx: click.Context,
    exporter: str,
    full: bool,
    chunk_size: str,
    versions: List[RepositoryVersionDefinition],
    start_versions: List[RepositoryVersionDefinition],
) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    pexport_ctx: PulpExportContext = ctx.find_object(PulpExportContext)
    the_exporter = pexport_ctx.find_exporter(exporter)
    params = {
        pexport_ctx.HREF: the_exporter["pulp_href"],
    }

    body: Dict[str, Any] = dict(full=full)

    if chunk_size:
        body["chunk_size"] = chunk_size

    vers_list = []
    for v in versions:
        vers_list.append(pexport_ctx.find_repository_version(v)["pulp_href"])
    if vers_list:
        body["versions"] = vers_list

    start_vers_list = []
    for v in start_versions:
        start_vers_list.append(pexport_ctx.find_repository_version(v)["pulp_href"])
    if start_vers_list:
        body["start_versions"] = start_vers_list

    result = pulp_ctx.call(pexport_ctx.CREATE_ID, parameters=params, body=body)
    pulp_ctx.output_result(result)
