import gettext
from typing import Iterable

import click

from pulpcore.cli.common.context import (
    EntityFieldDefinition,
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
    pass_pulp_context,
    registered_repository_contexts,
)
from pulpcore.cli.common.generic import (
    destroy_command,
    href_option,
    list_command,
    name_option,
    resource_option,
    show_command,
)
from pulpcore.cli.core.context import PulpExporterContext

_ = gettext.gettext


multi_repository_option = resource_option(
    "--repository",
    context_table=registered_repository_contexts,
    capabilities=["pulpexport"],
    multiple=True,
)


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
@click.option("--path", required=True)
@multi_repository_option
@click.option("--repository-href", multiple=True)
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    exporter_ctx: PulpExporterContext,
    name: str,
    path: str,
    repository: Iterable[EntityFieldDefinition],
    repository_href: Iterable[str],
) -> None:
    repo_hrefs = [
        repository_ctx.pulp_href
        for repository_ctx in repository
        if isinstance(repository_ctx, PulpEntityContext)
    ] + list(repository_href)

    params = {"name": name, "path": path, "repositories": repo_hrefs}
    result = exporter_ctx.create(body=params)
    pulp_ctx.output_result(result)


@pulp.command()
@name_option
@href_option
@click.option("--path")
@multi_repository_option
@click.option("--repository-href", multiple=True)
@pass_entity_context
@pass_pulp_context
def update(
    pulp_ctx: PulpContext,
    exporter_ctx: PulpExporterContext,
    path: str,
    repository: Iterable[EntityFieldDefinition],
    repository_href: Iterable[str],
) -> None:
    the_exporter = exporter_ctx.entity
    exporter_href = exporter_ctx.pulp_href

    if path:
        the_exporter["path"] = path

    if repository or repository_href:
        the_exporter["repositories"] = [
            repository_ctx.pulp_href
            for repository_ctx in repository
            if isinstance(repository_ctx, PulpEntityContext)
        ] + list(repository_href)

    exporter_ctx.update(exporter_href, the_exporter)
