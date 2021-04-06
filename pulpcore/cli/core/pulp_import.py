import gettext
from typing import Any, Dict

import click

from pulpcore.cli.common.context import (
    DEFAULT_LIMIT,
    PulpContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import Mutex, destroy_command, href_option, show_command
from pulpcore.cli.core.context import PulpImportContext, PulpImporterContext

_ = gettext.gettext


@click.group(name="import")
def pulp_import() -> None:
    pass


@pulp_import.group()
@pass_pulp_context
@click.pass_context
def pulp(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    ctx.obj = PulpImportContext(pulp_ctx)


lookup_options = [href_option]

pulp.add_command(show_command(decorators=lookup_options))
pulp.add_command(destroy_command(decorators=lookup_options))


@pulp.command()
@click.option("--importer", type=str, required=True, help=_("Name of owning PulpImporter"))
@click.option(
    "--limit", default=DEFAULT_LIMIT, type=int, help=_("Limit the number of imports to show.")
)
@click.option("--offset", default=0, type=int, help=_("Skip a number of imports to show."))
@pass_entity_context
@pass_pulp_context
def list(
    pulp_ctx: PulpContext,
    import_ctx: PulpImportContext,
    importer: str,
    limit: int,
    offset: int,
    **kwargs: Any
) -> None:
    params = {k: v for k, v in kwargs.items() if v is not None}
    importer_ctx = PulpImporterContext(pulp_ctx)
    import_ctx.importer = importer_ctx.find(name=importer)
    result = import_ctx.list(limit=limit, offset=offset, parameters=params)
    pulp_ctx.output_result(result)


@pulp.command()
@click.option("--importer", required=True)
@click.option("--toc", type=str, cls=Mutex, not_required_if=["path"])
@click.option("--path", type=str, cls=Mutex, not_required_if=["toc"])
@pass_entity_context
@pass_pulp_context
def run(
    pulp_ctx: PulpContext,
    import_ctx: PulpImportContext,
    importer: str,
    path: str,
    toc: str,
) -> None:
    importer_ctx = PulpImporterContext(pulp_ctx)
    import_ctx.importer = importer_ctx.find(name=importer)

    body: Dict[str, Any] = dict()
    if path:
        body["path"] = path

    if toc:
        body["toc"] = toc

    result = import_ctx.create(body=body)
    pulp_ctx.output_result(result)
