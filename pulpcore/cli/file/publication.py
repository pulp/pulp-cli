import click


@click.group()
@click.option(
    "-t",
    "--type",
    "publication_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@click.pass_context
def publication(ctx, publication_type):
    if publication_type == "file":
        ctx.obj.href_key = "file_file_publication_href"
        ctx.obj.list_id = "publications_file_file_list"
        ctx.obj.read_id = "publications_file_file_read"
        ctx.obj.create_id = "publications_file_file_create"
        ctx.obj.delete_id = "publications_file_file_delete"
    else:
        raise NotImplementedError()


@publication.command()
@click.pass_context
def list(ctx):
    result = ctx.obj.call(ctx.obj.list_id)
    ctx.obj.output_result(result)


@publication.command()
@click.option("--repository", required=True)
@click.pass_context
def create(ctx, repository):
    search_result = ctx.obj.call(
        "repositories_file_file_list", parameters={"name": repository, "limit": 1}
    )
    if search_result["count"] != 1:
        raise Exception(f"Repository '{repository}' not found.")
    body = {"repository": search_result["results"][0]["pulp_href"]}
    result = ctx.obj.call(ctx.obj.create_id, body=body)
    publication = ctx.obj.call(
        ctx.obj.read_id, parameters={ctx.obj.href_key: result["created_resources"][0]}
    )
    ctx.obj.output_result(publication)


@publication.command()
@click.option("--href", required=True)
@click.pass_context
def destroy(ctx, href):
    ctx.obj.call(ctx.obj.delete_id, parameters={ctx.obj.href_key: href})
