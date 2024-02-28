import typing as t

import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpImporterContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    destroy_command,
    href_option,
    list_command,
    name_option,
    pass_pulp_context,
    pulp_group,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext

pass_importer_context = click.make_pass_decorator(PulpImporterContext)


RepositoryMap = t.Tuple[str, str]  # source repo, destination repo

repo_map_option = click.option(
    "--repo-map",
    type=tuple([str, str]),
    multiple=True,
    help=_(
        "A map of source repository name to destination repository name (eg. --repo-map src dest)"
    ),
)


@pulp_group()
def importer() -> None:
    pass


@importer.group()
@pass_pulp_context
@click.pass_context
def pulp(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpImporterContext(pulp_ctx)


filter_options = [click.option("--name")]
lookup_options = [name_option, href_option]

pulp.add_command(list_command(decorators=filter_options))
pulp.add_command(show_command(decorators=lookup_options))
pulp.add_command(destroy_command(decorators=lookup_options))


@pulp.command()
@click.option("--name", required=True)
@repo_map_option
@pass_importer_context
@pass_pulp_context
def create(
    pulp_ctx: PulpCLIContext,
    importer_ctx: PulpImporterContext,
    name: str,
    repo_map: t.List[RepositoryMap],
) -> None:
    params: t.Dict[str, t.Union[str, t.Dict[str, str]]] = {"name": name}

    if repo_map:
        params["repo_mapping"] = {source: dest for source, dest in repo_map}

    result = importer_ctx.create(body=params)
    pulp_ctx.output_result(result)


@pulp.command()
@name_option
@href_option
@repo_map_option
@pass_importer_context
@pass_pulp_context
def update(
    pulp_ctx: PulpCLIContext,
    importer_ctx: PulpImporterContext,
    repo_map: t.List[RepositoryMap],
) -> None:
    payload = {}

    if repo_map:
        payload["repo_mapping"] = {source: dest for source, dest in repo_map}

    result = importer_ctx.update(body=payload)
    pulp_ctx.output_result(result)
