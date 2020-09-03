import click


@click.group()
@click.option("-t", "--type", "repo_type", type=click.Choice(["file"], case_sensitive=False), default="file")
@click.pass_context
def repository(ctx, repo_type):
    if repo_type == "file":
        ctx.obj.href_key = "file_file_repository_href"
        ctx.obj.list_id = "repositories_file_file_list"
        ctx.obj.create_id = "repositories_file_file_create"
        ctx.obj.update_id = "repositories_file_file_update"
        ctx.obj.delete_id = "repositories_file_file_delete"
        ctx.obj.sync_id = "repositories_file_file_sync"
    else:
        raise NotImplementedError()


@repository.command()
@click.pass_context
def list(ctx):
    result = ctx.obj.call(ctx.obj.list_id)
    ctx.obj.output_result(result)


def _find_remote(ctx, name):
    search_result = ctx.obj.call("remotes_file_file_list", parameters={"name": name, "limit": 1})
    if search_result["count"] != 1:
        raise Exception(f"Remote '{name}' not found.")
    remote = search_result["results"][0]
    return remote


@repository.command()
@click.option("--name", required=True)
@click.option("--description")
@click.option("--remote")
@click.pass_context
def create(ctx, name, description, remote):
    repository = {"name": name, "description": description}
    if remote:
        repository["remote"] = _find_remote(ctx, remote)["pulp_href"]

    result = ctx.obj.call(ctx.obj.create_id, body=repository)
    ctx.obj.output_result(result)


@repository.command()
@click.option("--name", required=True)
@click.option("--description")
@click.option("--remote")
@click.pass_context
def update(ctx, name, description, remote):
    search_result = ctx.obj.call(ctx.obj.list_id, parameters={"name": name, "limit": 1})
    if search_result["count"] != 1:
        raise Exception(f"Repository '{name}' not found.")
    repository = search_result["results"][0]
    repository_href = repository["pulp_href"]

    if description:
        if description != repository["description"]:
            repository["description"] = description

    if remote == "":
        # unset the remote
        repository["remote"] = ""
    elif remote:
        remote_href = _find_remote(ctx, remote)["pulp_href"]
        repository["remote"] = remote_href

    ctx.obj.call(ctx.obj.update_id, parameters={ctx.obj.href_key: repository_href}, body=repository)


@repository.command()
@click.option("--name", required=True)
@click.pass_context
def destroy(ctx, name):
    search_result = ctx.obj.call(ctx.obj.list_id, parameters={"name": name, "limit": 1})
    if search_result["count"] != 1:
        raise Exception(f"Repository '{name}' not found.")
    repository_href = search_result["results"][0]["pulp_href"]
    ctx.obj.call(ctx.obj.delete_id, parameters={ctx.obj.href_key: repository_href})


@repository.command()
@click.option("--name", required=True)
@click.option("--remote")
@click.pass_context
def sync(ctx, name, remote):
    body = {}

    search_result = ctx.obj.call(ctx.obj.list_id, parameters={"name": name, "limit": 1})
    if search_result["count"] != 1:
        raise Exception(f"Repository '{name}' not found.")
    repository_href = search_result["results"][0]["pulp_href"]

    if remote:
        remote_href = _find_remote(ctx, remote)["pulp_href"]
        body["remote"] = remote_href

    ctx.obj.call(ctx.obj.sync_id, parameters={ctx.obj.href_key: repository_href}, body=body)
