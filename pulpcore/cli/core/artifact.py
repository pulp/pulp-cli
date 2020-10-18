from typing import IO

import hashlib
import os

import click

from pulpcore.cli.common import PulpContext


@click.group()
def artifact() -> None:
    pass


@artifact.command()
@click.option("--sha256")
@click.pass_context
def list(ctx: click.Context, **kwargs: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    params = {k: v for k, v in kwargs.items() if v is not None}
    result = pulp_ctx.call("artifacts_list", parameters=params)
    pulp_ctx.output_result(result)


@artifact.command()
@click.option("--file", type=click.File("rb"), required=True)
@click.option(
    "--chunk-size", default=1000000, type=int, help="Chunk size in bytes (default is 1 MB)"
)
@click.pass_context
def upload(ctx: click.Context, file: IO[bytes], chunk_size: int) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    start = 0
    size = os.path.getsize(file.name)
    sha256 = hashlib.sha256()
    upload_href = pulp_ctx.call("uploads_create", body={"size": size})["pulp_href"]
    click.echo(f"Uploading file {file.name}", err=True)

    try:
        while start < size:
            end = min(size, start + chunk_size) - 1
            file.seek(start)
            chunk = file.read(chunk_size)
            sha256.update(chunk)
            range_header = f"bytes {start}-{end}/{size}"
            pulp_ctx.call(
                "uploads_update",
                parameters={"upload_href": upload_href, "Content-Range": range_header},
                body={"sha256": hashlib.sha256(chunk).hexdigest()},
                uploads={"file": chunk},
            )
            start += chunk_size
            click.echo(".", nl=False, err=True)

        click.echo("Upload complete. Creating artifact.", err=True)
        pulp_ctx.call(
            "uploads_commit",
            parameters={"upload_href": upload_href},
            body={"sha256": sha256.hexdigest()},
        )
    except Exception as e:
        pulp_ctx.call("uploads_delete", parameters={"upload_href": upload_href})
        raise e
