import click


@click.group()
@click.option(
    "-t",
    "--type",
    "distribution_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@click.pass_context
def distribution(ctx, distribution_type):
    if distribution_type == "file":
        ctx.obj.href_key = "file_file_distribution_href"
        ctx.obj.list_id = "distributions_file_file_list"
        ctx.obj.read_id = "distributions_file_file_read"
        ctx.obj.create_id = "distributions_file_file_create"
        ctx.obj.delete_id = "distributions_file_file_delete"
    else:
        raise NotImplementedError()


@distribution.command()
@click.pass_context
def list(ctx):
    result = ctx.obj.call(ctx.obj.list_id)
    ctx.obj.output_result(result)


@distribution.command()
@click.option("--name", required=True)
@click.option("--base-path", required=True)
@click.option("--publication")
@click.pass_context
def create(ctx, name, base_path, publication):
    body = {"name": name, "base_path": base_path}
    if publication:
        body["publication"] = publication
    result = ctx.obj.call(ctx.obj.create_id, body=body)
    distribution = ctx.obj.call(
        ctx.obj.read_id, parameters={ctx.obj.href_key: result["created_resources"][0]}
    )
    ctx.obj.output_result(distribution)


@distribution.command()
@click.option("--name", required=True)
@click.pass_context
def destroy(ctx, name):
    search_result = ctx.obj.call(ctx.obj.list_id, parameters={"name": name, "limit": 1})
    if search_result["count"] != 1:
        raise Exception(f"Distribution '{name}' not found.")
    distribution_href = search_result["results"][0]["pulp_href"]
    ctx.obj.call(ctx.obj.delete_id, parameters={ctx.obj.href_key: distribution_href})
