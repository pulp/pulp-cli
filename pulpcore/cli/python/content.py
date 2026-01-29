import json
import typing as t

import click

from pulp_glue.common.context import PluginRequirement, PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpArtifactContext
from pulp_glue.python.context import (
    PulpPythonContentContext,
    PulpPythonProvenanceContext,
    PulpPythonRepositoryContext,
)

from pulp_cli.generic import (
    PulpCLIContext,
    chunk_size_option,
    create_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    load_json_callback,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    pulp_option,
    resource_option,
    show_command,
    type_option,
)

translation = get_translation(__package__)
_ = translation.gettext


def _sha256_artifact_callback(
    ctx: click.Context, param: click.Parameter, value: str | None
) -> str | PulpEntityContext | None:
    # Pass None and "" verbatim
    if value:
        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx is not None
        return PulpArtifactContext(pulp_ctx, entity={"sha256": value})
    return value


def _attestation_callback(
    ctx: click.Context, param: click.Parameter, value: t.Iterable[str] | None
) -> str | None:
    """Callback to process multiple attestation values and combine them into a list."""
    if not value:
        return None
    result = []
    for attestation_value in value:
        # Use load_json_callback to process each value (supports JSON strings and file paths)
        processed = load_json_callback(ctx, param, attestation_value)
        # If it's already a list, extend; otherwise append
        if isinstance(processed, list):
            result.extend(processed)
        else:
            result.append(processed)
    return json.dumps(result)


repository_option = resource_option(
    "--repository",
    default_plugin="python",
    default_type="python",
    context_table={
        "python:python": PulpPythonRepositoryContext,
    },
    href_pattern=PulpPythonRepositoryContext.HREF_PATTERN,
    help=_(
        "Repository to add the content to in the form '[[<plugin>:]<resource_type>:]<name>' or by "
        "href."
    ),
)

package_option = resource_option(
    "--package",
    default_plugin="python",
    default_type="packages",
    lookup_key="sha256",
    context_table={
        "python:packages": PulpPythonContentContext,
    },
    href_pattern=PulpPythonContentContext.HREF_PATTERN,
    help=_(
        "Package to associate the provenance with in the form"
        "'[[<plugin>:]<resource_type>:]<sha256>' or by href/prn."
    ),
    allowed_with_contexts=(PulpPythonProvenanceContext,),
)


@pulp_group()
@type_option(
    choices={
        "package": PulpPythonContentContext,
        "provenance": PulpPythonProvenanceContext,
    },
    default="package",
    case_sensitive=False,
)
def content() -> None:
    pass


create_options = [
    pulp_option(
        "--relative-path",
        required=True,
        help=_("Exact name of file"),
        allowed_with_contexts=(PulpPythonContentContext,),
    ),
    pulp_option(
        "--file",
        type=click.File("rb"),
        help=_("Path to the file to create {entity} from"),
    ),
    click.option(
        "--sha256",
        "artifact",
        help=_("Digest of the artifact to use [deprecated]"),
        callback=_sha256_artifact_callback,
    ),
    pulp_option(
        "--file-url",
        help=_("Remote url to download and create {entity} from"),
        needs_plugins=[PluginRequirement("core", specifier=">=3.56.1")],
    ),
    pulp_option(
        "--attestation",
        "attestations",
        multiple=True,
        callback=_attestation_callback,
        needs_plugins=[PluginRequirement("python", specifier=">=3.22.0")],
        help=_(
            "A JSON object containing an attestation for the package. Can be a JSON string or a "
            "file path prefixed with '@'. Can be specified multiple times."
        ),
        allowed_with_contexts=(PulpPythonContentContext,),
    ),
    repository_option,
]
provenance_create_options = [
    package_option,
    pulp_option(
        "--verify/--no-verify",
        default=True,
        needs_plugins=[PluginRequirement("python", specifier=">=3.22.0")],
        help=_("Verify the provenance"),
        allowed_with_contexts=(PulpPythonProvenanceContext,),
    ),
]
lookup_options = [href_option]
content.add_command(
    list_command(
        decorators=[
            pulp_option("--filename", allowed_with_contexts=(PulpPythonContentContext,)),
            pulp_option("--sha256"),
            label_select_option,
            package_option,
        ]
    )
)
content.add_command(show_command(decorators=lookup_options))
content.add_command(create_command(decorators=create_options + provenance_create_options))
content.add_command(
    label_command(
        decorators=lookup_options,
        need_plugins=[PluginRequirement("core", specifier=">=3.73.2")],
    )
)


@content.command(allowed_with_contexts=(PulpPythonContentContext,))
@click.option("--relative-path", required=True, help=_("Exact name of file"))
@click.option("--file", type=click.File("rb"), required=True, help=_("Path to file"))
@chunk_size_option
@pulp_option(
    "--attestation",
    "attestations",
    multiple=True,
    callback=_attestation_callback,
    needs_plugins=[PluginRequirement("python", specifier=">=3.22.0")],
    help=_(
        "A JSON object containing an attestation for the package. Can be a JSON string or a file"
        " path prefixed with '@'. Can be specified multiple times."
    ),
)
@repository_option
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpCLIContext,
    entity_ctx: PulpEntityContext,
    /,
    relative_path: str,
    file: t.IO[bytes],
    chunk_size: int,
    attestations: list[t.Any] | None,
    repository: PulpPythonRepositoryContext | None,
) -> None:
    """Create a Python package content unit through uploading a file [deprecated]"""
    assert isinstance(entity_ctx, PulpPythonContentContext)

    result = entity_ctx.upload(
        relative_path=relative_path,
        file=file,
        chunk_size=chunk_size,
        repository=repository,
        attestations=attestations,
    )
    pulp_ctx.output_result(result)
