from typing import IO

import hashlib
import os
from copy import deepcopy
import click

from pulpcore.cli.common.generic import (
    list_entities,
    show_by_href,
)
from pulpcore.cli.common.context import (
    pass_pulp_context,
    PulpContext,
    PulpEntityContext,
)


class PulpArtifactContext(PulpEntityContext):
    HREF: str = "artifact_href"
    LIST_ID: str = "artifacts_list"
    READ_ID: str = "artifacts_read"


@click.group()
@pass_pulp_context
@click.pass_context
def artifact(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpArtifactContext(pulp_ctx)


# deepcopy to not effect other list subcommands
list_artifacts = deepcopy(list_entities)
click.option("--sha256")(list_artifacts)
artifact.add_command(list_artifacts)


artifact.add_command(show_by_href)


@artifact.command()
@click.option("--file", type=click.File("rb"), required=True)
@click.option(
    "--chunk-size", default=1000000, type=int, help="Chunk size in bytes (default is 1 MB)"
)
@pass_pulp_context
def upload(pulp_ctx: PulpContext, file: IO[bytes], chunk_size: int) -> None:
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
