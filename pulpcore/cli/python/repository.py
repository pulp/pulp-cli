from typing import Optional, Union

import click

from pulpcore.cli.common.context import (
    PulpContext,
    PulpEntityContext,
    PulpRepositoryContext,
    pass_pulp_context,
    pass_repository_context,
)
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    show_command,
    update_command,
    version_command,
)
from pulpcore.cli.python.context import (
    PulpPythonContentContext,
    PulpPythonRemoteContext,
    PulpPythonRepositoryContext,
)


def _remote_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[Union[str, PulpEntityContext]]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx: PulpContext = ctx.find_object(PulpContext)
        return PulpPythonRemoteContext(pulp_ctx, entity={"name": value})
    return value


@click.group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["python"], case_sensitive=False),
    default="python",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpContext, repo_type: str) -> None:
    if repo_type == "python":
        ctx.obj = PulpPythonRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option]
create_options = [
    click.option("--name", required=True),
    click.option("--description"),
    click.option("--remote", callback=_remote_callback),
]
update_options = [
    click.option("--description"),
    click.option("--remote", callback=_remote_callback),
]

repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(destroy_command(decorators=lookup_options))
repository.add_command(create_command(decorators=create_options))
repository.add_command(update_command(decorators=lookup_options + update_options))
repository.add_command(version_command())
repository.add_command(label_command())


@repository.command()
@name_option
@href_option
@click.option("--remote", callback=_remote_callback)
@pass_repository_context
@pass_pulp_context
def sync(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    remote: Optional[Union[str, PulpEntityContext]],
) -> None:
    repository = repository_ctx.entity
    repository_href = repository_ctx.pulp_href

    body = {}

    if isinstance(remote, PulpEntityContext):
        body["remote"] = remote.pulp_href
    elif repository["remote"] is None:
        name = repository["name"]
        raise click.ClickException(
            f"Repository '{name}' does not have a default remote. Please specify with '--remote'."
        )

    repository_ctx.sync(
        href=repository_href,
        body=body,
    )


@repository.command()
@name_option
@href_option
@click.option("--filename", required=True)
@click.option("--base-version", type=int)
@pass_repository_context
@pass_pulp_context
def add(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    filename: str,
    base_version: Optional[int],
) -> None:
    repository_href = repository_ctx.pulp_href

    base_version_href: Optional[str]
    if base_version is not None:
        base_version_href = f"{repository_href}versions/{base_version}/"
    else:
        base_version_href = None

    content_href = PulpPythonContentContext(pulp_ctx, entity={"filename": filename}).pulp_href

    repository_ctx.modify(
        href=repository_href,
        add_content=[content_href],
        base_version=base_version_href,
    )


@repository.command()
@name_option
@href_option
@click.option("--filename", required=True)
@click.option("--base-version", type=int)
@pass_repository_context
@pass_pulp_context
def remove(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    filename: str,
    base_version: Optional[int],
) -> None:
    repository_href = repository_ctx.pulp_href

    base_version_href: Optional[str]
    if base_version is not None:
        base_version_href = f"{repository_href}versions/{base_version}/"
    else:
        base_version_href = None

    content_href = PulpPythonContentContext(pulp_ctx, entity={"filename": filename}).pulp_href

    repository_ctx.modify(
        href=repository_href,
        remove_content=[content_href],
        base_version=base_version_href,
    )
