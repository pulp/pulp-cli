import click


@click.group()
@click.option(
    "-t",
    "--type",
    "remote_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@click.pass_context
def remote(ctx, remote_type):
    if remote_type == "file":
        ctx.obj.href_key = "file_file_remote_href"
        ctx.obj.list_id = "remotes_file_file_list"
        ctx.obj.create_id = "remotes_file_file_create"
        ctx.obj.update_id = "remotes_file_file_update"
        ctx.obj.delete_id = "remotes_file_file_delete"
    else:
        raise NotImplementedError()


@remote.command()
@click.pass_context
def list(ctx):
    result = ctx.obj.call(ctx.obj.list_id)
    ctx.obj.output_result(result)


@remote.command()
@click.option("--name", required=True)
@click.option("--url")
@click.pass_context
def create(ctx, name, url):
    remote = {"name": name, "url": url}
    result = ctx.obj.call(ctx.obj.create_id, body=remote)
    ctx.obj.output_result(result)


@remote.command()
@click.option("--name", required=True)
@click.pass_context
def destroy(ctx, name):
    search_result = ctx.obj.call(ctx.obj.list_id, parameters={"name": name, "limit": 1})
    if search_result["count"] != 1:
        raise click.ClickException(f"Remote '{name}' not found.")
    remote_href = search_result["results"][0]["pulp_href"]
    ctx.obj.call(ctx.obj.delete_id, parameters={ctx.obj.href_key: remote_href})
