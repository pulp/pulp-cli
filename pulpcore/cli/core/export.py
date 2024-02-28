import re
import typing as t

import click
from pulp_glue.common.context import (
    DEFAULT_LIMIT,
    EntityDefinition,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpExportContext, PulpExporterContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    destroy_command,
    href_option,
    pass_pulp_context,
    pulp_group,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext

pass_export_context = click.make_pass_decorator(PulpExportContext)


def _version_list_callback(
    ctx: click.Context, param: click.Parameter, value: t.Iterable[t.Tuple[str, int]]
) -> t.Iterable[PulpRepositoryVersionContext]:
    result = []
    pulp_ctx = ctx.find_object(PulpCLIContext)
    assert pulp_ctx is not None
    for item in value:
        pulp_href: t.Optional[str] = None
        entity: t.Optional[EntityDefinition] = None

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
        context_class = PulpRepositoryContext.TYPE_REGISTRY.get(plugin + ":" + resource_type)
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

        entity_ctx = repository_ctx.get_version_context(number=item[1])
        result.append(entity_ctx)

    return result


@pulp_group()
def export() -> None:
    pass


@export.group()
@pass_pulp_context
@click.pass_context
def pulp(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    ctx.obj = PulpExportContext(pulp_ctx)


lookup_options = [href_option]

pulp.add_command(show_command(decorators=lookup_options))
pulp.add_command(destroy_command(decorators=lookup_options))


# This is a mypy bug getting confused with positional args
# https://github.com/python/mypy/issues/15037
@pulp.command()  # type: ignore [arg-type]
@click.option("--exporter", type=str, required=True, help=_("Name of owning PulpExporter"))
@click.option(
    "--limit", default=DEFAULT_LIMIT, type=int, help=_("Limit the number of exporters to show.")
)
@click.option("--offset", default=0, type=int, help=_("Skip a number of exporters to show."))
@pass_export_context
@pass_pulp_context
def list(
    pulp_ctx: PulpCLIContext,
    export_ctx: PulpExportContext,
    exporter: str,
    limit: int,
    offset: int,
    **kwargs: t.Any,
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
@pass_export_context
@pass_pulp_context
def run(
    pulp_ctx: PulpCLIContext,
    export_ctx: PulpExportContext,
    exporter: str,
    full: bool,
    chunk_size: str,
    versions: t.Iterable[PulpRepositoryVersionContext],
    start_versions: t.Iterable[PulpRepositoryVersionContext],
) -> None:
    exporter_ctx = PulpExporterContext(pulp_ctx)
    export_ctx.exporter = exporter_ctx.find(name=exporter)

    body: t.Dict[str, t.Any] = dict(full=full)

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
