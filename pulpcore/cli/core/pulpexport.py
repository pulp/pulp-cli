from typing import Any, List, Tuple
import click
from pulpcore.cli.common import main

RepositoryDefinition = Tuple[str, str]  # name, pulp_type


@main.group()
@click.pass_context
def pulpexporter(ctx: click.Context) -> None:
    ctx.obj.href_key = "pulp_exporter_href"
    ctx.obj.href = "pulp_exporter_href"
    ctx.obj.list_id = "exporters_core_pulp_list"
    ctx.obj.delete_id = "exporters_core_pulp_delete"
    ctx.obj.create_id = "exporters_core_pulp_create"
    ctx.obj.update_id = "exporters_core_pulp_update"
    ctx.obj.repository_find = {
        "file": "repositories_file_file_list",
        "rpm": "repositories_rpm_rpm_list",
    }


def _find_exporter(ctx: click.Context, name: str) -> Any:
    search_result = ctx.obj.call(ctx.obj.list_id, parameters={"name": name, "limit": 1})
    if search_result["count"] != 1:
        raise click.ClickException(f"PulpExporter '{name}' not found.")
    exporter = search_result["results"][0]
    return exporter


def _find_repository_href(ctx: click.Context, definition: RepositoryDefinition) -> Any:
    name, repo_type = definition
    if repo_type in ctx.obj.repository_find:
        search_result = ctx.obj.call(
            ctx.obj.repository_find[repo_type], parameters={"name": name, "limit": 1}
        )
    else:
        raise click.ClickException(f"PulpExporter 'Repository-type '{repo_type}' not supported!")

    if search_result["count"] != 1:
        raise click.ClickException(f"Repository '{name}/{repo_type}' not found.")

    repository = search_result["results"][0]
    return repository["pulp_href"]


@pulpexporter.command()
@click.option("--name", type=str)
@click.pass_context
def list(ctx: click.Context, **kwargs: Any) -> None:
    params = {k: v for k, v in kwargs.items() if v is not None}
    result = ctx.obj.call(ctx.obj.list_id, parameters=params)
    ctx.obj.output_result(result)


@pulpexporter.command()
@click.option("--name", required=True)
@click.pass_context
def delete(ctx: click.Context, name: str) -> None:
    exporter_href = _find_exporter(ctx, name)["pulp_href"]
    result = ctx.obj.call(ctx.obj.delete_id, parameters={ctx.obj.href_key: exporter_href})
    ctx.obj.output_result(result)


@pulpexporter.command()
@click.option("--name", required=True)
@click.option("--path", type=str)
@click.option("--repository", type=tuple([str, str]), multiple=True)
@click.pass_context
def create(
    ctx: click.Context, name: str, path: str, repository: List[RepositoryDefinition]
) -> None:
    repo_hrefs = []
    for repo_tuple in repository:
        repo_hrefs.append(_find_repository_href(ctx, repo_tuple))

    params = {"name": name, "path": path, "repositories": repo_hrefs}

    result = ctx.obj.call(ctx.obj.create_id, body=params)
    ctx.obj.output_result(result)


@pulpexporter.command()
@click.option("--name", required=True)
@click.option("--path")
@click.option("--repository", type=tuple([str, str]), multiple=True)
@click.pass_context
def update(
    ctx: click.Context, name: str, path: str, repository: List[RepositoryDefinition]
) -> None:
    exporter = _find_exporter(ctx, name)
    exporter_href = exporter["pulp_href"]

    if path:
        exporter["path"] = path

    if repository:
        repo_hrefs = []
        for repo_tuple in repository:
            repo_hrefs.append(_find_repository_href(ctx, repo_tuple))
        exporter["repositories"] = repo_hrefs

    ctx.obj.call(
        ctx.obj.update_id,
        parameters={ctx.obj.href_key: exporter_href},
        body=exporter,
    )
