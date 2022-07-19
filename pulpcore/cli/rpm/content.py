import os
from typing import IO, Any, Dict, Optional, Union

import click

from pulpcore.cli.common.context import (
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import (
    chunk_size_option,
    create_command,
    href_option,
    list_command,
    pulp_group,
    pulp_option,
    show_command,
    type_option,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import PulpArtifactContext, PulpUploadContext
from pulpcore.cli.rpm.context import (
    PulpRpmAdvisoryContext,
    PulpRpmDistributionTreeContext,
    PulpRpmModulemdContext,
    PulpRpmModulemdDefaultsContext,
    PulpRpmPackageCategoryContext,
    PulpRpmPackageContext,
    PulpRpmPackageEnvironmentContext,
    PulpRpmPackageGroupContext,
    PulpRpmPackageLangpacksContext,
    PulpRpmRepoMetadataFileContext,
)

translation = get_translation(__name__)
_ = translation.gettext


def _relative_path_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.entity = {"relative_path": value}
    return value


def _sha256_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.entity = {"sha256": value}
    return value


def _sha256_artifact_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[Union[str, PulpEntityContext]]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx = ctx.find_object(PulpContext)
        assert pulp_ctx is not None
        return PulpArtifactContext(pulp_ctx, entity={"sha256": value})
    return value


@pulp_group()
@type_option(
    choices={
        "package": PulpRpmPackageContext,
        "advisory": PulpRpmAdvisoryContext,
        "distribution_tree": PulpRpmDistributionTreeContext,
        "modulemd_defaults": PulpRpmModulemdDefaultsContext,
        "modulemd": PulpRpmModulemdContext,
        "package_category": PulpRpmPackageCategoryContext,
        "package_environment": PulpRpmPackageEnvironmentContext,
        "package_group": PulpRpmPackageGroupContext,
        "package_langpack": PulpRpmPackageLangpacksContext,
        "repo_metadata_file": PulpRpmRepoMetadataFileContext,
    },
    default="package",
    case_sensitive=False,
)
def content() -> None:
    pass


list_options = [
    pulp_option("--exclude_fields"),
    pulp_option("--fields"),
    pulp_option("--repository-version"),
    pulp_option("--arch", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--arch-in", "arch__in", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--arch-ne", "arch__ne", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--epoch", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--epoch-in", "epoch__in", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--epoch-ne", "epoch__ne", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--id", allowed_with_contexts=(PulpRpmPackageContext, PulpRpmAdvisoryContext)),
    pulp_option(
        "--id-in", "id__in", allowed_with_contexts=(PulpRpmPackageContext, PulpRpmAdvisoryContext)
    ),
    pulp_option("--module", allowed_with_contexts=(PulpRpmModulemdDefaultsContext,)),
    pulp_option(
        "--module-in", "module__in", allowed_with_contexts=(PulpRpmModulemdDefaultsContext,)
    ),
    pulp_option("--name", allowed_with_contexts=(PulpRpmPackageContext, PulpRpmModulemdContext)),
    pulp_option(
        "--name-in",
        "name__in",
        allowed_with_contexts=(PulpRpmPackageContext, PulpRpmModulemdContext),
    ),
    pulp_option(
        "--name-ne",
        "name__ne",
        allowed_with_contexts=(PulpRpmPackageContext, PulpRpmModulemdContext),
    ),
    pulp_option("--package-href", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--pkgId", allowed_with_contexts=(PulpRpmPackageContext, PulpRpmModulemdContext)),
    pulp_option(
        "--pkgId-in",
        "pkgId__in",
        allowed_with_contexts=(PulpRpmPackageContext, PulpRpmModulemdContext),
    ),
    pulp_option("--release", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--release-in", "release__in", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--release-ne", "release__ne", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--severity", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option("--severity-in", "severity__in", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option("--severity-ne", "severity__ne", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option(
        "--sha256",
        allowed_with_contexts=(
            PulpRpmPackageContext,
            PulpRpmModulemdDefaultsContext,
            PulpRpmModulemdContext,
        ),
    ),
    pulp_option("--status", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option("--status-in", "status__in", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option("--status-ne", "status__ne", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option(
        "--stream", allowed_with_contexts=(PulpRpmModulemdDefaultsContext, PulpRpmModulemdContext)
    ),
    pulp_option(
        "--stream-in",
        "stream__in",
        allowed_with_contexts=(PulpRpmModulemdDefaultsContext, PulpRpmModulemdContext),
    ),
    pulp_option("--type", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option("--type-in", "type__in", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option("--type-ne", "type__ne", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option("--version", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--version-in", "version__in", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--version-ne", "version__ne", allowed_with_contexts=(PulpRpmPackageContext,)),
]
lookup_options = [
    href_option,
    pulp_option(
        "--relative-path",
        callback=_relative_path_callback,
        expose_value=False,
        allowed_with_contexts=(PulpRpmPackageContext,),
    ),
    pulp_option(
        "--sha256",
        callback=_sha256_callback,
        expose_value=False,
        allowed_with_contexts=(
            PulpRpmPackageContext,
            PulpRpmModulemdDefaultsContext,
            PulpRpmModulemdContext,
        ),
    ),
]

content.add_command(list_command(decorators=list_options))
content.add_command(show_command(decorators=lookup_options))
# create assumes "there exists an Artifact..."
# create is defined for package, modulemd and modulemd_defaults.  The implications for modulemd
# and modulemd_defaults are generally not what the user expects. Therefore, leaving those two
# endpoints hidden until we have a better handle on what we should really be doing.
# See https://github.com/pulp/pulp_rpm/issues/2229 and https://github.com/pulp/pulp_rpm/issues/2534
create_options = [
    pulp_option(
        "--relative-path",
        required=True,
        allowed_with_contexts=(PulpRpmPackageContext,),
    ),
    pulp_option(
        "--sha256",
        "artifact",
        required=True,
        help=_("Digest of the artifact to use"),
        callback=_sha256_artifact_callback,
        allowed_with_contexts=(PulpRpmPackageContext,),
    ),
]
content.add_command(
    create_command(
        decorators=create_options,
        allowed_with_contexts=(PulpRpmPackageContext,),
    )
)


# upload takes a file-argument and creates the entity from it.
# upload currently only works for advisory/package,
# see https://github.com/pulp/pulp_rpm/issues/2534
@content.command(
    allowed_with_contexts=(
        PulpRpmPackageContext,
        PulpRpmAdvisoryContext,
    )
)
@chunk_size_option
@pulp_option(
    "--relative-path",
    required=True,
    help=_("Relative path within a distribution of the entity"),
    allowed_with_contexts=(PulpRpmPackageContext,),
)
@pulp_option(
    "--file",
    type=click.File("rb"),
    required=True,
    help=_("An RPM binary"),
    allowed_with_contexts=(PulpRpmPackageContext,),
)
@pulp_option(
    "--file",
    type=click.File("rb"),
    required=True,
    help=_("An advisory JSON file."),
    allowed_with_contexts=(PulpRpmAdvisoryContext,),
)
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpContext,
    entity_ctx: Union[
        PulpRpmPackageContext,
        PulpRpmAdvisoryContext,
    ],
    file: IO[bytes],
    chunk_size: int,
    **kwargs: Any,
) -> None:
    """Create a content unit by uploading a file"""
    size = os.path.getsize(file.name)
    body: Dict[str, Any] = {}
    uploads: Dict[str, IO[bytes]] = {}
    if isinstance(entity_ctx, PulpRpmPackageContext):
        if chunk_size > size:
            uploads["file"] = file
        elif pulp_ctx.has_plugin(PluginRequirement("core", min="3.20")):
            upload_href = PulpUploadContext(pulp_ctx).upload_file(file, chunk_size)
            body["upload"] = upload_href
        else:
            artifact_href = PulpArtifactContext(pulp_ctx).upload(file, chunk_size)
            body["artifact"] = artifact_href
        body.update(kwargs)
    elif isinstance(entity_ctx, PulpRpmAdvisoryContext):
        uploads["file"] = file
    else:
        raise NotImplementedError()
    result = entity_ctx.create(body=body, uploads=uploads)
    pulp_ctx.output_result(result)
