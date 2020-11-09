from typing import IO

import hashlib
import os

import click

from pulpcore.cli.common import DEFAULT_LIMIT, show_by_href, PulpContext, PulpEntityContext


class PulpArtifactContext(PulpEntityContext):
    HREF: str = "artifact_href"
    LIST_ID: str = "artifacts_list"
    READ_ID: str = "artifacts_read"


@click.group()
@click.pass_context
def artifact(ctx: click.Context) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    ctx.obj = PulpArtifactContext(pulp_ctx)


@artifact.command()
@click.option(
    "--limit", default=DEFAULT_LIMIT, type=int, help="Limit the number of artifacts to show."
)
@click.option("--offset", default=0, type=int, help="Skip a number of tasks to show.")
@click.option("--sha256")
@click.pass_context
def list(ctx: click.Context, limit: int, offset: int, **kwargs: str) -> None:
    pulp_ctx: PulpContext = ctx.find_object(PulpContext)
    artifact_ctx: PulpArtifactContext = ctx.find_object(PulpArtifactContext)

    params = {k: v for k, v in kwargs.items() if v is not None}
    result = artifact_ctx.list(limit=limit, offset=offset, parameters=params)
    pulp_ctx.output_result(result)


artifact.add_command(show_by_href)


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
