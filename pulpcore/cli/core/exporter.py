from typing import Any, Dict, Iterable

import click

from pulpcore.cli.common.context import (
    EntityFieldDefinition,
    PulpEntityContext,
    PulpRepositoryContext,
    registered_repository_contexts,
)
from pulpcore.cli.common.generic import (
    PulpCLIContext,
    destroy_command,
    href_option,
    list_command,
    name_option,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    resource_option,
    show_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import PulpExporterContext

translation = get_translation(__name__)
_ = translation.gettext


multi_repository_option = resource_option(
    "--repository",
    context_table=registered_repository_contexts,
    capabilities=["pulpexport"],
    multiple=True,
    href_pattern=PulpRepositoryContext.HREF_PATTERN,
    help=_(
        "Repository to export from in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
        " Can be called multiple times."
    ),
)


@pulp_group()
def exporter() -> None:
    pass


@exporter.group()
@pass_pulp_context
@click.pass_context
def pulp(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
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
    pulp_ctx: PulpCLIContext,
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
@click.option("--repository-href", multiple=True)  # This should be deprecated
@pass_entity_context
@pass_pulp_context
def update(
    pulp_ctx: PulpCLIContext,
    exporter_ctx: PulpExporterContext,
    path: str,
    repository: Iterable[EntityFieldDefinition],
    repository_href: Iterable[str],
) -> None:
    payload: Dict[str, Any] = {}

    if path:
        payload["path"] = path

    if repository or repository_href:
        payload["repositories"] = [
            repository_ctx.pulp_href
            for repository_ctx in repository
            if isinstance(repository_ctx, PulpEntityContext)
        ] + list(repository_href)

    exporter_ctx.update(body=payload)
