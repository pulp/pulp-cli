import gettext
from copy import deepcopy
from typing import Dict, List, Tuple, Union

import click

from pulpcore.cli.common.context import PulpContext, pass_entity_context, pass_pulp_context
from pulpcore.cli.common.generic import destroy_by_name, list_entities, show_by_name
from pulpcore.cli.core.context import PulpImporterContext

_ = gettext.gettext

RepositoryMap = Tuple[str, str]  # source repo, destination repo

repo_map_option = click.option(
    "--repo-map",
    type=tuple([str, str]),
    multiple=True,
    help=_(
        "A map of source repository name to destination repository name (eg. --repo-map src dest)"
    ),
)


@click.group()
def importer() -> None:
    pass


@importer.group()
@pass_pulp_context
@click.pass_context
def pulp(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpImporterContext(pulp_ctx)


list_pulp_exporters = deepcopy(list_entities)
click.option("--name", type=str)(list_pulp_exporters)
pulp.add_command(list_pulp_exporters)


@pulp.command()
@click.option("--name", required=True)
@repo_map_option
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    importer_ctx: PulpImporterContext,
    name: str,
    repo_map: List[RepositoryMap],
) -> None:
    params: Dict[str, Union[str, Dict[str, str]]] = {"name": name}

    if repo_map:
        params["repo_mapping"] = {source: dest for source, dest in repo_map}

    result = importer_ctx.create(body=params)
    pulp_ctx.output_result(result)


pulp.add_command(show_by_name)


@pulp.command()
@click.option("--name", required=True)
@repo_map_option
@pass_entity_context
@pass_pulp_context
def update(
    pulp_ctx: PulpContext,
    importer_ctx: PulpImporterContext,
    name: str,
    repo_map: List[RepositoryMap],
) -> None:
    importer = importer_ctx.find(name=name)
    importer_href = importer["pulp_href"]

    if repo_map:
        importer["repo_mapping"] = {source: dest for source, dest in repo_map}

    result = importer_ctx.update(importer_href, importer)
    pulp_ctx.output_result(result)


pulp.add_command(destroy_by_name)
