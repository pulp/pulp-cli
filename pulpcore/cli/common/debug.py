import sys
from typing import IO, Any, Dict, Iterable, Optional

import click

from pulpcore.cli.common.context import PluginRequirement, PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import load_json_callback, pulp_group
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group(help=_("Commands useful for debugging"))
def debug() -> None:
    """
    Commands useful for debugging.
    """


@debug.command()
@click.option("--name", required=True)
@click.option("--min-version", help=_("Succeed only if the installed version is not smaller."))
@click.option("--max-version", help=_("Succeed only if the installed version is smaller."))
@pass_pulp_context
def has_plugin(
    pulp_ctx: PulpContext, name: str, min_version: Optional[str], max_version: Optional[str]
) -> None:
    """
    Check whether a specific plugin is installed on the server.
    """
    available = pulp_ctx.has_plugin(PluginRequirement(name, min_version, max_version))
    pulp_ctx.output_result(available)
    sys.exit(0 if available else 1)


@debug.command()
@pass_pulp_context
def task_summary(pulp_ctx: PulpContext) -> None:
    """
    List a summary of tasks by status.
    """
    from pulpcore.cli.core.context import PulpTaskContext

    result = PulpTaskContext(pulp_ctx).summary()
    pulp_ctx.output_result(result)


@debug.group(name="openapi")
def openapi_group() -> None:
    pass


@openapi_group.command()
@pass_pulp_context
def schema(pulp_ctx: PulpContext) -> None:
    """
    Print the openapi schema of the server.
    """
    pulp_ctx.output_result(pulp_ctx.api.api_spec)


@openapi_group.command()
@click.option("--id", "operation_id", required=True, help=_("Operation ID in openapi schema"))
@pass_pulp_context
def operation(pulp_ctx: PulpContext, operation_id: str) -> None:
    """
    Print the openapi schema of the server.
    """
    method: str
    path: str
    try:
        method, path = pulp_ctx.api.operations[operation_id]
    except KeyError:
        raise click.ClickException(
            _("No operation with id {operation_id} found.").format(operation_id=operation_id)
        )
    result = {
        "method": method,
        "path": path,
        "operation": pulp_ctx.api.api_spec["paths"][path][method],
    }
    pulp_ctx.output_result(result)


@openapi_group.command()
@pass_pulp_context
def operation_ids(pulp_ctx: PulpContext) -> None:
    """
    Print a list of available operation-ids.
    """
    pulp_ctx.output_result(list(pulp_ctx.api.operations.keys()))


@openapi_group.command()
@click.option("--id", "operation_id", required=True, help=_("Operation ID in openapi schema"))
@click.option("--parameter", "parameters", multiple=True)
@click.option("--body", callback=load_json_callback)
@click.option("--upload", "uploads", type=click.File("rb"), multiple=True)
@pass_pulp_context
def call(
    pulp_ctx: PulpContext,
    operation_id: str,
    parameters: Iterable[str],
    body: Any,
    uploads: Iterable[IO[bytes]],
) -> None:
    """
    Make a REST call by operation-id.

    WARNING: Danger ahead!
    """
    try:
        params: Dict[str, str] = dict(parameter.partition("=")[::2] for parameter in parameters)
    except ValueError:
        raise click.ClickException("Parameters must be in the form <key>=<value>.")
    uploads_dict: Dict[str, bytes] = {file.name: file.read() for file in uploads}
    result = pulp_ctx.call(operation_id, parameters=params, body=body, uploads=uploads_dict)
    pulp_ctx.output_result(result)
