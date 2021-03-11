import gettext
from typing import List

import click

from pulpcore.cli.common.context import (
    PulpContext,
    RepositoryDefinition,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import (
    destroy_command,
    href_option,
    list_command,
    name_option,
    show_command,
)
from pulpcore.cli.core.context import PulpExporterContext

_ = gettext.gettext


@click.group()
def exporter() -> None:
    pass


@exporter.group()
@pass_pulp_context
@click.pass_context
def pulp(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpExporterContext(pulp_ctx)


filter_options = [click.option("--name")]
lookup_options = [name_option, href_option]

pulp.add_command(list_command(decorators=filter_options))
pulp.add_command(show_command(decorators=lookup_options))
pulp.add_command(destroy_command(decorators=lookup_options))


@pulp.command()
@click.option("--name", required=True)
@click.option("--path", type=str, required=True)
@click.option("--repository", type=tuple([str, str]), multiple=True, required=True)
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    exporter_ctx: PulpExporterContext,
    name: str,
    path: str,
    repository: List[RepositoryDefinition],
) -> None:
    repo_hrefs = []
    for repo_tuple in repository:
        repo_hrefs.append(exporter_ctx.find_repository(repo_tuple)["pulp_href"])

    params = {"name": name, "path": path, "repositories": repo_hrefs}
    result = exporter_ctx.create(body=params)
    pulp_ctx.output_result(result)


@pulp.command(deprecated=True)
@click.option("--name", required=True, help=_("Name of the PulpExporter"))
@pass_entity_context
@pass_pulp_context
def read(pulp_ctx: PulpContext, exporter_ctx: PulpExporterContext, name: str) -> None:
    """Shows details of an artifact."""
    exporter_href = exporter_ctx.find(name=name)["pulp_href"]
    entity = exporter_ctx.show(exporter_href)
    pulp_ctx.output_result(entity)


@pulp.command()
@click.option("--name", required=True)
@click.option("--path")
@click.option("--repository", type=tuple([str, str]), multiple=True)
@pass_entity_context
@pass_pulp_context
def update(
    pulp_ctx: PulpContext,
    exporter_ctx: PulpExporterContext,
    name: str,
    path: str,
    repository: List[RepositoryDefinition],
) -> None:
    the_exporter = exporter_ctx.find(name=name)
    exporter_href = the_exporter["pulp_href"]

    if path:
        the_exporter["path"] = path

    if repository:
        repo_hrefs = []
        for repo_tuple in repository:
            repo_hrefs.append(exporter_ctx.find_repository(repo_tuple)["pulp_href"])
        the_exporter["repositories"] = repo_hrefs

    result = exporter_ctx.update(exporter_href, the_exporter)
    pulp_ctx.output_result(result)


@pulp.command(deprecated=True)
@click.option("--name", required=True)
@pass_entity_context
@pass_pulp_context
def delete(pulp_ctx: PulpContext, exporter_ctx: PulpExporterContext, name: str) -> None:
    exporter_href = exporter_ctx.find(name=name)["pulp_href"]
    result = exporter_ctx.delete(exporter_href)
    pulp_ctx.output_result(result)
