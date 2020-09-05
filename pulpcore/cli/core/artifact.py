import hashlib
import os

import click


@click.group()
@click.pass_context
def artifact(ctx):
    pass


@artifact.command()
@click.option("--sha256")
@click.pass_context
def list(ctx, **kwargs):
    params = {k: v for k, v in kwargs.items() if v is not None}
    result = ctx.obj.call("artifacts_list", parameters=params)
    ctx.obj.output_result(result)


@artifact.command()
@click.option("--file", type=click.File('rb'), required=True)
@click.option("--chunk-size", default=1000000, help="Chunk size in bytes (default is 1 MB)")
@click.pass_context
def upload(ctx, file, chunk_size):
    start = 0
    size = os.path.getsize(file.name)
    sha256 = hashlib.sha256()
    upload_href = ctx.obj.call("uploads_create", body={"size": size})["pulp_href"]
    click.echo(f"Uploading file {file.name}", err=True)

    try:
        while start < size:
            end = min(size, start + chunk_size) - 1
            file.seek(start)
            chunk = file.read(chunk_size)
            sha256.update(chunk)
            range_header = f"bytes {start}-{end}/{size}"
            ctx.obj.call("uploads_update",
                         parameters={"upload_href": upload_href, "Content-Range": range_header},
                         body={"sha256": hashlib.sha256(chunk).hexdigest()},
                         uploads={"file": chunk},
                         )
            start += chunk_size
            click.echo(".", nl=False, err=True)

        click.echo("Upload complete. Creating artifact.", err=True)
        ctx.obj.call("uploads_commit",
                     parameters={"upload_href": upload_href},
                     body={"sha256": sha256.hexdigest()},
                     )
    except Exception as e:
        ctx.obj.call("uploads_delete", parameters={"upload_href": upload_href})
        raise e
