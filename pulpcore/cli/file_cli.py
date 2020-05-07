import click
from pulpcore.client.pulp_file import (
    ApiClient,
    RepositoriesFileApi,
    FileFileRepository,
)

from pulpcore.cli import main


@main.group()
@click.pass_context
def file(ctx):
    ctx.obj.file_client = ApiClient(ctx.obj.api_config)


@file.group()
@click.option("-t", "--type", "repo_type", type=click.Choice(["file"], case_sensitive=False), default="file")
@click.pass_context
def repository(ctx, repo_type):
    if repo_type == "file":
        ctx.obj.repositories_api = RepositoriesFileApi(ctx.obj.file_client)
        ctx.obj.repository_class = FileFileRepository
    else:
        raise NotImplementedError()


@repository.command()
@click.pass_context
def list(ctx):
    result = ctx.obj.repositories_api.list()
    click.echo(result)


@repository.command()
@click.option("--name", required=True)
@click.pass_context
def create(ctx, name):
    repository = ctx.obj.repository_class(name=name)
    result = ctx.obj.repositories_api.create(repository)
    click.echo(result)


@repository.command()
@click.option("--name", required=True)
@click.pass_context
def destroy(ctx, name):
    search_result = ctx.obj.repositories_api.list(name=name).results
    if len(search_result) != 1:
        raise Exception(f"Repository '{name}' not found.")
    task_href = ctx.obj.repositories_api.delete(search_result[0].pulp_href).task
    click.echo(f"Started task {task_href}")
    ctx.obj.wait_for_task(task_href)
    click.echo("Done.")
