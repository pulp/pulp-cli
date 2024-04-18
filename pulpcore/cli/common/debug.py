import typing as t
from types import ModuleType

import click
from packaging.specifiers import SpecifierSet
from pulp_glue.common.context import PluginRequirement
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    load_json_callback,
    pass_pulp_context,
    pulp_group,
)

try:
    import IPython
except ImportError:
    IPYTHON_AVAILABLE = False
else:
    IPYTHON_AVAILABLE = True

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group(help=_("Commands useful for debugging"))
def debug() -> None:
    """
    Commands useful for debugging.
    """


if IPYTHON_AVAILABLE:

    @debug.command()
    @pass_pulp_context
    @click.pass_context
    def ipython(
        ctx: click.Context,
        pulp_ctx: PulpCLIContext,
    ) -> None:
        """
        Drop into an interactive python shell.
        Prepopulated symbols:
          - click
          - PluginRequirement
          - ctx: click.Context
          - pulp_ctx: PulpContext
        """
        user_ns: t.Dict[str, t.Any] = {
            # modules
            "click": click,
            # Classes
            "PluginRequirement": PluginRequirement,
            # Objects
            "ctx": ctx,
            "pulp_ctx": pulp_ctx,
        }
        IPython.start_ipython(argv=[], user_ns=user_ns)  # type:ignore


@debug.command()
@click.option("--name", required=True)
@click.option("--specifier", help=_("Succeed only if the installed version is contained."))
@pass_pulp_context
@click.pass_context
def has_cli_plugin(
    ctx: click.Context,
    pulp_ctx: PulpCLIContext,
    name: str,
    specifier: t.Optional[str],
) -> None:
    """
    Check whether a specific cli plugin is installed.
    """
    available = False
    plugin: t.Optional[ModuleType] = ctx.meta["pulp_cli.plugins"].get(name)
    if plugin:
        if specifier:
            version = getattr(plugin, "__version__", None)
            if version:
                available = version in SpecifierSet(specifier, prereleases=True)
            else:
                raise click.ClickException(
                    _("CLI Plugin '{}' does not advertise a version.").format(name)
                )
        else:
            available = True
    pulp_ctx.output_result(available)
    ctx.exit(0 if available else 1)


@debug.command()
@click.option("--name", required=True)
@click.option("--specifier", help=_("Succeed only if the installed version is contained."))
@pass_pulp_context
@click.pass_context
def has_plugin(
    ctx: click.Context,
    pulp_ctx: PulpCLIContext,
    name: str,
    specifier: t.Optional[str],
) -> None:
    """
    Check whether a specific plugin is installed on the server.
    """
    available = pulp_ctx.has_plugin(PluginRequirement(name, specifier=specifier))
    pulp_ctx.output_result(available)
    ctx.exit(0 if available else 1)


@debug.group(name="openapi")
def openapi_group() -> None:
    pass


@openapi_group.command()
@pass_pulp_context
def spec(pulp_ctx: PulpCLIContext) -> None:
    """
    Print the openapi schema of the server.
    """
    pulp_ctx.output_result(pulp_ctx.api.api_spec)


@openapi_group.command()
@pass_pulp_context
def info(pulp_ctx: PulpCLIContext) -> None:
    """
    Print info block.
    """
    pulp_ctx.output_result(pulp_ctx.api.api_spec["info"])


@openapi_group.command()
@pass_pulp_context
def security_schemes(pulp_ctx: PulpCLIContext) -> None:
    """
    Print info block.
    """
    pulp_ctx.output_result(pulp_ctx.api.api_spec["components"]["securitySchemes"])


@openapi_group.command()
@click.option("--id", "operation_id", required=True, help=_("Operation ID in openapi schema"))
@pass_pulp_context
def operation(pulp_ctx: PulpCLIContext, operation_id: str) -> None:
    """
    Print the spec of the operation.
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
def operation_ids(pulp_ctx: PulpCLIContext) -> None:
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
    pulp_ctx: PulpCLIContext,
    operation_id: str,
    parameters: t.Iterable[str],
    body: t.Any,
    uploads: t.Iterable[t.IO[bytes]],
) -> None:
    """
    Make a REST call by operation-id.

    WARNING: Danger ahead!
    """
    try:
        params: t.Dict[str, str] = dict(parameter.partition("=")[::2] for parameter in parameters)
    except ValueError:
        raise click.ClickException("Parameters must be in the form <key>=<value>.")
    if uploads:
        body = body or {}
        body.update({file.name: file for file in uploads})
    result = pulp_ctx.call(operation_id, parameters=params, body=body)
    pulp_ctx.output_result(result)


@openapi_group.command()
@click.option(
    "--name", "schema_name", required=True, help=_("Component schema name in openapi schema")
)
@pass_pulp_context
def schema(pulp_ctx: PulpCLIContext, schema_name: str) -> None:
    """
    Print the spec of the schema component.
    """
    try:
        result = pulp_ctx.api.api_spec["components"]["schemas"][schema_name]
    except KeyError:
        raise click.ClickException(
            _("No schema component with name {schema_name} found.").format(schema_name=schema_name)
        )
    pulp_ctx.output_result(result)


@openapi_group.command()
@pass_pulp_context
def schema_names(pulp_ctx: PulpCLIContext) -> None:
    """
    Print a list of available schema component names.
    """
    pulp_ctx.output_result(list(pulp_ctx.api.api_spec["components"]["schemas"].keys()))
