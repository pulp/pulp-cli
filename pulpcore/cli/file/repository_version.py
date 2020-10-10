import click

from .repository import repository


def _find_repository(ctx, repository):
    if ctx.parent.parent.params["repo_type"] == "file":
        repo_list_id = "repositories_file_file_list"
    else:
        raise NotImplementedError()

    search_result = ctx.obj.call(
        repo_list_id, parameters={"name": repository, "limit": 1}
    )
    if search_result["count"] != 1:
        raise click.ClickException(f"Repository '{repository}' not found.")

    return search_result["results"][0]


@repository.group()
@click.pass_context
def version(ctx):
    if ctx.parent.params["repo_type"] == "file":
        ctx.obj.href_key = "file_file_repository_version_href"
        ctx.obj.list_id = "repositories_file_file_versions_list"
        ctx.obj.delete_id = "repositories_file_file_versions_delete"
    else:
        raise NotImplementedError()


@version.command()
@click.option("--repository", required=True)
@click.pass_context
def list(ctx, repository):
    repo_href = _find_repository(ctx, repository)["pulp_href"]
    result = ctx.obj.call(
        ctx.obj.list_id, parameters={"file_file_repository_href": repo_href}
    )
    ctx.obj.output_result(result)


@version.command()
@click.option("--repository", required=True)
@click.option("--version", required=True)
@click.pass_context
def destroy(ctx, repository, version):
    repo_href = _find_repository(ctx, repository)["pulp_href"]
    repo_version_href = f"{repo_href}versions/{version}"
    result = ctx.obj.call(
        ctx.obj.delete_id, parameters={ctx.obj.href_key: repo_version_href}
    )
    ctx.obj.output_result(result)
