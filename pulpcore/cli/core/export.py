import re
from typing import Any, Dict, Iterable, Optional, Tuple

import click

from pulpcore.cli.common.context import (
    DEFAULT_LIMIT,
    EntityDefinition,
    PulpContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    pass_entity_context,
    pass_pulp_context,
    registered_repository_contexts,
)
from pulpcore.cli.common.generic import destroy_command, href_option, show_command
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import PulpExportContext, PulpExporterContext

translation = get_translation(__name__)
_ = translation.gettext


def _version_list_callback(
    ctx: click.Context, param: click.Parameter, value: Iterable[Tuple[str, int]]
) -> Iterable[PulpRepositoryVersionContext]:
    result = []
    pulp_ctx = ctx.find_object(PulpContext)
    assert pulp_ctx is not None
    for item in value:
        pulp_href: Optional[str] = None
        entity: Optional[EntityDefinition] = None

        if item[0].startswith("/"):
            pattern = rf"^{pulp_ctx.api_path}{PulpRepositoryContext.HREF_PATTERN}"
            match = re.match(pattern, item[0])
            if match is None:
                raise click.ClickException(
                    _("'{value}' is not a valid href for {option_name}.").format(
                        value=value, option_name=param.name
                    )
                )
            match_groups = match.groupdict(default="")
            plugin = match_groups.get("plugin", "")
            resource_type = match_groups.get("resource_type", "")
            pulp_href = item[0]
        else:
            plugin, resource_type, identifier = item[0].split(":", maxsplit=2)
            if not identifier:
                raise click.ClickException(_("Repositories must be specified with plugin and type"))
            entity = {"name": identifier}
        context_class = registered_repository_contexts.get(plugin + ":" + resource_type)
        if context_class is None:
            raise click.ClickException(
                _(
                    "The type '{plugin}:{resource_type}' "
                    "is not valid for the {option_name} option."
                ).format(plugin=plugin, resource_type=resource_type, option_name=param.name)
            )
        repository_ctx: PulpRepositoryContext = context_class(
            pulp_ctx, pulp_href=pulp_href, entity=entity
        )

        if not repository_ctx.capable("pulpexport"):
            raise click.ClickException(
                _(
                    "The type '{plugin}:{resource_type}' "
                    "does not support the '{capability}' capability."
                ).format(plugin=plugin, resource_type=resource_type, capability="export")
            )

        entity_ctx = repository_ctx.get_version_context()
        entity_ctx.pulp_href = f"{repository_ctx.entity['versions_href']}{item[1]}/"
        result.append(entity_ctx)

    return result


@click.group()
def export() -> None:
    pass


@export.group()
@pass_pulp_context
@click.pass_context
def pulp(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpExportContext(pulp_ctx)


lookup_options = [href_option]

pulp.add_command(show_command(decorators=lookup_options))
pulp.add_command(destroy_command(decorators=lookup_options))


@pulp.command()
@click.option("--exporter", type=str, required=True, help=_("Name of owning PulpExporter"))
@click.option(
    "--limit", default=DEFAULT_LIMIT, type=int, help=_("Limit the number of exporters to show.")
)
@click.option("--offset", default=0, type=int, help=_("Skip a number of exporters to show."))
@pass_entity_context
@pass_pulp_context
def list(
    pulp_ctx: PulpContext,
    export_ctx: PulpExportContext,
    exporter: str,
    limit: int,
    offset: int,
    **kwargs: Any,
) -> None:
    params = {k: v for k, v in kwargs.items() if v is not None}
    exporter_ctx = PulpExporterContext(pulp_ctx)
    export_ctx.exporter = exporter_ctx.find(name=exporter)
    result = export_ctx.list(limit=limit, offset=offset, parameters=params)
    pulp_ctx.output_result(result)


@pulp.command()
@click.option("--exporter", required=True)
@click.option("--full", type=bool, default=True)
@click.option("--chunk-size", type=str, help=_("Examples: 512MB, 1GB"))
@click.option("--versions", type=tuple([str, int]), multiple=True, callback=_version_list_callback)
@click.option(
    "--start-versions", type=tuple([str, int]), multiple=True, callback=_version_list_callback
)
@pass_entity_context
@pass_pulp_context
def run(
    pulp_ctx: PulpContext,
    export_ctx: PulpExportContext,
    exporter: str,
    full: bool,
    chunk_size: str,
    versions: Iterable[PulpRepositoryVersionContext],
    start_versions: Iterable[PulpRepositoryVersionContext],
) -> None:
    exporter_ctx = PulpExporterContext(pulp_ctx)
    export_ctx.exporter = exporter_ctx.find(name=exporter)

    body: Dict[str, Any] = dict(full=full)

    if chunk_size:
        body["chunk_size"] = chunk_size

    vers_list = []
    for v in versions:
        vers_list.append(v.pulp_href)
    if vers_list:
        body["versions"] = vers_list

    start_vers_list = []
    for v in start_versions:
        start_vers_list.append(v.pulp_href)
    if start_vers_list:
        body["start_versions"] = start_vers_list

    result = export_ctx.create(body=body)
    pulp_ctx.output_result(result)
