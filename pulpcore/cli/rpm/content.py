import glob
import typing as t
from uuid import uuid4

import click
from pulp_glue.common.context import PluginRequirement, PulpContentContext, PulpEntityContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpArtifactContext
from pulp_glue.rpm.context import (
    PulpRpmAdvisoryContext,
    PulpRpmCopyContext,
    PulpRpmDistributionTreeContext,
    PulpRpmModulemdContext,
    PulpRpmModulemdDefaultsContext,
    PulpRpmPackageCategoryContext,
    PulpRpmPackageContext,
    PulpRpmPackageEnvironmentContext,
    PulpRpmPackageGroupContext,
    PulpRpmPackageLangpacksContext,
    PulpRpmPublicationContext,
    PulpRpmRepoMetadataFileContext,
    PulpRpmRepositoryContext,
)

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    chunk_size_option,
    create_command,
    exclude_field_option,
    field_option,
    href_option,
    list_command,
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
    ctx: click.Context, param: click.Parameter, value: t.Optional[str]
) -> t.Optional[t.Union[str, PulpEntityContext]]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx is not None
        return PulpArtifactContext(pulp_ctx, entity={"sha256": value})
    return value


repository_option = resource_option(
    "--repository",
    default_plugin="rpm",
    default_type="rpm",
    context_table={
        "rpm:rpm": PulpRpmRepositoryContext,
    },
    href_pattern=PulpRpmRepositoryContext.HREF_PATTERN,
    help=_(
        "Repository to add the content to in the form '[[<plugin>:]<resource_type>:]<name>' or by "
        "href."
    ),
    allowed_with_contexts=(PulpRpmPackageContext,),
)


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
    field_option,
    exclude_field_option,
    pulp_option("--repository-version"),
    pulp_option("--arch", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option(
        "--arch-contains",
        "arch__contains",
        allowed_with_contexts=(PulpRpmPackageContext,),
        needs_plugins=[PluginRequirement("rpm", specifier=">=3.20.0")],
    ),
    pulp_option(
        "--arch-in",
        "arch__in",
        multiple=True,
        allowed_with_contexts=(PulpRpmPackageContext,),
        needs_plugins=[PluginRequirement("rpm", specifier=">=3.20.0")],
    ),
    pulp_option("--arch-ne", "arch__ne", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option(
        "--arch-startswith",
        "arch__startswith",
        allowed_with_contexts=(PulpRpmPackageContext,),
        needs_plugins=[PluginRequirement("rpm", specifier=">=3.20.0")],
    ),
    pulp_option("--epoch", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option(
        "--epoch-in", "epoch__in", multiple=True, allowed_with_contexts=(PulpRpmPackageContext,)
    ),
    pulp_option("--epoch-ne", "epoch__ne", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--id", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option(
        "--id-in", "id__in", multiple=True, allowed_with_contexts=(PulpRpmAdvisoryContext,)
    ),
    pulp_option("--module", allowed_with_contexts=(PulpRpmModulemdDefaultsContext,)),
    pulp_option(
        "--module-in",
        "module__in",
        multiple=True,
        allowed_with_contexts=(PulpRpmModulemdDefaultsContext,),
    ),
    pulp_option("--name", allowed_with_contexts=(PulpRpmPackageContext, PulpRpmModulemdContext)),
    pulp_option(
        "--name-contains",
        "name__contains",
        allowed_with_contexts=(PulpRpmPackageContext, PulpRpmModulemdContext),
        needs_plugins=[PluginRequirement("rpm", specifier=">=3.20.0")],
    ),
    pulp_option(
        "--name-in",
        "name__in",
        multiple=True,
        allowed_with_contexts=(PulpRpmPackageContext, PulpRpmModulemdContext),
    ),
    pulp_option(
        "--name-ne",
        "name__ne",
        allowed_with_contexts=(PulpRpmPackageContext, PulpRpmModulemdContext),
    ),
    pulp_option(
        "--name-startswith",
        "name__startswith",
        allowed_with_contexts=(PulpRpmPackageContext, PulpRpmModulemdContext),
        needs_plugins=[PluginRequirement("rpm", specifier=">=3.20.0")],
    ),
    pulp_option("--package-href", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option("--pkgId", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option(
        "--pkgId-in",
        "pkgId__in",
        multiple=True,
        allowed_with_contexts=(PulpRpmPackageContext,),
    ),
    pulp_option("--release", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option(
        "--release-contains",
        "release__contains",
        allowed_with_contexts=(PulpRpmPackageContext,),
        needs_plugins=[PluginRequirement("rpm", specifier=">=3.20.0")],
    ),
    pulp_option(
        "--release-in",
        "release__in",
        multiple=True,
        allowed_with_contexts=(PulpRpmPackageContext,),
        needs_plugins=[PluginRequirement("rpm", specifier=">=3.20.0")],
    ),
    pulp_option("--release-ne", "release__ne", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option(
        "--release-startswith",
        "release__startswith",
        allowed_with_contexts=(PulpRpmPackageContext,),
    ),
    pulp_option("--severity", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option(
        "--severity-in",
        "severity__in",
        multiple=True,
        allowed_with_contexts=(PulpRpmAdvisoryContext,),
    ),
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
    pulp_option(
        "--status-in", "status__in", multiple=True, allowed_with_contexts=(PulpRpmAdvisoryContext,)
    ),
    pulp_option("--status-ne", "status__ne", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option(
        "--stream", allowed_with_contexts=(PulpRpmModulemdDefaultsContext, PulpRpmModulemdContext)
    ),
    pulp_option(
        "--stream-in",
        "stream__in",
        multiple=True,
        allowed_with_contexts=(PulpRpmModulemdDefaultsContext, PulpRpmModulemdContext),
    ),
    pulp_option("--type", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option(
        "--type-in", "type__in", multiple=True, allowed_with_contexts=(PulpRpmAdvisoryContext,)
    ),
    pulp_option("--type-ne", "type__ne", allowed_with_contexts=(PulpRpmAdvisoryContext,)),
    pulp_option("--version", allowed_with_contexts=(PulpRpmPackageContext,)),
    pulp_option(
        "--version-in", "version__in", multiple=True, allowed_with_contexts=(PulpRpmPackageContext,)
    ),
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
    repository_option,
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
# This is a mypy bug getting confused with positional args
# https://github.com/python/mypy/issues/15037
@content.command(  # type: ignore [arg-type]
    allowed_with_contexts=(
        PulpRpmPackageContext,
        PulpRpmAdvisoryContext,
    )
)
@repository_option
@pulp_option(
    "--file",
    type=click.File("rb"),
    required=True,
    help=_("An advisory JSON file."),
    allowed_with_contexts=(PulpRpmAdvisoryContext,),
)
@pulp_option(
    "--file",
    type=click.File("rb"),
    help=_("An RPM binary. One of --file or --directory is required."),
    allowed_with_contexts=(PulpRpmPackageContext,),
    required=False,
)
@pulp_option(
    "--relative-path",
    help=_("Relative path within a distribution of the entity"),
    allowed_with_contexts=(PulpRpmPackageContext,),
)
@pulp_option(
    "--directory",
    type=click.Path(exists=True, readable=True, file_okay=False, dir_okay=True),
    help=_(
        "A directory containing RPM binaries named .rpm. "
        "A --repository is required for this directive. "
        "One of --file or --directory is required."
    ),
    allowed_with_contexts=(PulpRpmPackageContext,),
    required=False,
)
@pulp_option(
    "--publish/--no-publish",
    type=bool,
    show_default=True,
    default=True,
    help=_(
        "If --publish, once all files are uploaded into the destination repository,"
        " trigger a publish on the resulting repository-version."
    ),
    allowed_with_contexts=(PulpRpmPackageContext,),
)
@pulp_option(
    "--use-temp-repository",
    type=bool,
    is_flag=True,
    show_default=True,
    default=False,
    help=_(
        "In conjunction with --directory, create and upload into a temporary repository, "
        " then copy results into the specified destination as an atomic operation."
    ),
    allowed_with_contexts=(PulpRpmPackageContext,),
)
@chunk_size_option
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpCLIContext,
    entity_ctx: PulpEntityContext,
    file: t.IO[bytes],
    chunk_size: int,
    **kwargs: t.Any,
) -> None:
    """Create a content unit by uploading a file or files"""
    if isinstance(entity_ctx, PulpRpmPackageContext):
        directory = kwargs.get("directory")
        # Sanity: one of file|directory required
        if (not (file or directory)) or (file and directory):
            raise click.ClickException(
                _("You must specify one (and only one) of --file or --directory.")
            )

        # Sanity: If directory, repository required
        final_dest_repo_ctx = kwargs["repository"]
        if directory and not final_dest_repo_ctx:
            raise click.ClickException(
                _("You must specify a --repository to use --directory uploads.")
            )

        # Sanity: ignore publish|use_temp unless directory has been specified
        use_tmp = final_dest_repo_ctx and kwargs["use_temp_repository"]
        do_publish = final_dest_repo_ctx and kwargs["publish"]

        # Sanity: ignore relative_path if directory specified
        if directory and kwargs["relative_path"]:
            raise click.ClickException(
                _("relative_path may not be specified on --directory uploads.")
            )

        if file:
            # Single-file upload
            result = entity_ctx.upload(
                file=file,
                chunk_size=chunk_size,
                repository=final_dest_repo_ctx,
                relative_path=kwargs["relative_path"],
            )
        else:
            # Upload a directory-full of RPMs
            try:
                dest_repo_ctx = _determine_upload_repository(final_dest_repo_ctx, pulp_ctx, use_tmp)
                result = _upload_rpms(entity_ctx, dest_repo_ctx, directory, chunk_size)
                if use_tmp:
                    result = _copy_to_final(dest_repo_ctx, final_dest_repo_ctx, pulp_ctx)
            finally:
                if use_tmp and dest_repo_ctx:
                    # Remove the tmp-upload repo
                    dest_repo_ctx.delete()

        final_version_number = _latest_version_number(final_dest_repo_ctx)
        if final_version_number:
            click.echo(
                _(
                    "Created new version {} in {}".format(
                        final_version_number, final_dest_repo_ctx.entity["name"]
                    )
                ),
                err=True,
            )

        if do_publish:
            # Publish to generate metadata for the resulting repo-version
            click.echo(
                _("Publishing repository {}.".format(final_dest_repo_ctx.entity["name"])), err=True
            )
            publication_ctx = PulpRpmPublicationContext(pulp_ctx)
            body = {"repository": final_dest_repo_ctx.pulp_href, "version": final_version_number}
            result = publication_ctx.create(body)

    elif isinstance(entity_ctx, PulpRpmAdvisoryContext):
        body = {"file": file}
        result = entity_ctx.create(body=body)
    else:
        raise NotImplementedError()
    pulp_ctx.output_result(result)


def _latest_version_number(final_dest_repo_ctx: PulpRpmRepositoryContext) -> t.Optional[int]:
    if final_dest_repo_ctx:
        repo_result = final_dest_repo_ctx.show()
        version_number = int(repo_result["latest_version_href"].split("/")[-2])
        return version_number
    else:
        return None


def _copy_to_final(
    dest_repo_ctx: PulpRpmRepositoryContext,
    final_dest_repo_ctx: PulpRpmRepositoryContext,
    pulp_ctx: PulpCLIContext,
) -> t.Any:
    # Get a current-representation of the upload-repo, so we have its latest-version
    repo_result = dest_repo_ctx.show()
    # Copy everything from tmp-repo into final-dest
    copy_config = [
        {
            "source_repo_version": repo_result["latest_version_href"],
            "dest_repo": final_dest_repo_ctx.pulp_href,
        }
    ]
    copy_ctx = PulpRpmCopyContext(pulp_ctx)
    click.echo(
        _("Creating new version of repository {}".format(final_dest_repo_ctx.entity["name"])),
        err=True,
    )
    result = copy_ctx.copy(config=copy_config)
    return result


def _upload_rpms(
    entity_ctx: PulpContentContext,
    dest_repo_ctx: PulpRpmRepositoryContext,
    directory: t.Any,
    chunk_size: int,
) -> t.Any:
    rpms_path = f"{directory}/*.rpm"
    rpm_names = glob.glob(rpms_path)
    if not rpm_names:
        raise click.ClickException(_("Directory {} has no .rpm files in it.").format(directory))
    click.echo(
        _(
            "About to upload {} files for {}.".format(
                len(rpm_names),
                dest_repo_ctx.entity["name"],
            )
        ),
        err=True,
    )
    # Upload all *.rpm into the destination
    successful_uploads = 0
    for name in rpm_names:
        try:
            with open(name, "rb") as rpm:
                result = entity_ctx.upload(
                    file=rpm, chunk_size=chunk_size, repository=dest_repo_ctx
                )
                click.echo(_("Uploaded {}...").format(name), err=True)
            successful_uploads += 1
        except Exception as e:
            click.echo(_("Failed to upload file {} : {}".format(name, e)), err=True)

    if not successful_uploads:
        raise click.ClickException(_("No successful uploads using directory {}!").format(directory))
    else:
        return result


def _determine_upload_repository(
    final_dest_repo_ctx: PulpRpmRepositoryContext, pulp_ctx: PulpCLIContext, use_tmp: bool
) -> PulpRpmRepositoryContext:
    if use_tmp:
        dest_repo_ctx = PulpRpmRepositoryContext(pulp_ctx)
        body: t.Dict[str, t.Any] = {
            "name": f"uploadtmp_{final_dest_repo_ctx.entity['name']}_{uuid4()}",
            "retain_repo_versions": 1,
            "autopublish": False,
        }
        dest_repo_ctx.create(body=body)
        return dest_repo_ctx
    else:
        return final_dest_repo_ctx
