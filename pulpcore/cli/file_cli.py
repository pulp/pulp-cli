import click

from pulpcore.cli import main


@main.group()
@click.pass_context
def file(ctx):
    pass


@file.group()
@click.option("-t", "--type", "repo_type", type=click.Choice(["file"], case_sensitive=False), default="file")
@click.pass_context
def repository(ctx, repo_type):
    if repo_type == "file":
        ctx.obj.href_key = "file_file_repository_href"
        ctx.obj.list_id = "repositories_file_file_list"
        ctx.obj.create_id = "repositories_file_file_create"
        ctx.obj.update_id = "repositories_file_file_update"
        ctx.obj.delete_id = "repositories_file_file_delete"
    else:
        raise NotImplementedError()


@repository.command()
@click.pass_context
def list(ctx):
    result = ctx.obj.api.call(ctx.obj.list_id)
    ctx.obj.output_result(result)


@repository.command()
@click.option("--name", required=True)
@click.option("--description")
@click.pass_context
def create(ctx, name, description):
    repository = {"name": name, "description": description}
    result = ctx.obj.api.call(ctx.obj.create_id, body=repository)
    ctx.obj.output_result(result)


@repository.command()
@click.option("--name", required=True)
@click.option("--description")
@click.pass_context
def update(ctx, name, description):
    search_result = ctx.obj.api.call(ctx.obj.list_id, parameters={"name": name, "limit": 1})
    if search_result["count"] != 1:
        raise Exception(f"Repository '{name}' not found.")
    repository = search_result["results"][0]
    repository_href = repository["pulp_href"]
    if description:
        if description != repository["description"]:
            repository["description"] = description
    task_href = ctx.obj.api.call(ctx.obj.update_id, parameters={ctx.obj.href_key: repository_href}, body=repository)["task"]
    click.echo(f"Started task {task_href}")
    ctx.obj.wait_for_task(task_href)
    click.echo("Done.")


@repository.command()
@click.option("--name", required=True)
@click.pass_context
def destroy(ctx, name):
    search_result = ctx.obj.api.call(ctx.obj.list_id, parameters={"name": name, "limit": 1})
    if search_result["count"] != 1:
        raise Exception(f"Repository '{name}' not found.")
    repository_href = search_result["results"][0]["pulp_href"]
    task_href = ctx.obj.api.call(ctx.obj.delete_id, parameters={ctx.obj.href_key: repository_href})["task"]
    click.echo(f"Started task {task_href}")
    ctx.obj.wait_for_task(task_href)
    click.echo("Done.")
