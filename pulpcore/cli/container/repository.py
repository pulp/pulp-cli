import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import click
from pulp_glue.common.context import (
    EntityFieldDefinition,
    PulpContext,
    PulpRemoteContext,
    PulpRepositoryContext,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.container.context import (
    PulpContainerBaseRepositoryContext,
    PulpContainerBlobContext,
    PulpContainerManifestContext,
    PulpContainerPushRepositoryContext,
    PulpContainerRemoteContext,
    PulpContainerRepositoryContext,
    PulpContainerTagContext,
)
from pulp_glue.core.context import PulpArtifactContext

from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    load_json_callback,
    name_option,
    pass_pulp_context,
    pass_repository_context,
    pulp_group,
    pulp_labels_option,
    repository_content_command,
    repository_href_option,
    repository_lookup_option,
    resource_option,
    retained_versions_option,
    role_command,
    show_command,
    type_option,
    update_command,
    version_command,
)
from pulpcore.cli.container.content import show_options
from pulpcore.cli.core.generic import task_command

translation = get_translation(__name__)
_ = translation.gettext
VALID_TAG_REGEX = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"


def _tag_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if len(value) == 0:
        raise click.ClickException(_("Please pass a non empty tag name."))
    if re.match(VALID_TAG_REGEX, value) is None:
        raise click.ClickException(_("Please pass a valid tag."))

    return value


def _directory_or_json_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Union[Dict[str, str], Path, None]:
    if not value:
        return None
    uvalue: Union[Dict[str, str], Path]
    try:
        uvalue = load_json_callback(ctx, param, value)
    except click.ClickException:
        uvalue = Path(value)
        if not uvalue.exists() or not uvalue.is_dir():
            raise click.ClickException(_("{} is not a valid directory").format(value))

    return uvalue


source_option = resource_option(
    "--source",
    default_plugin="container",
    default_type="container",
    context_table={
        "container:container": PulpContainerRepositoryContext,
        "container:push": PulpContainerPushRepositoryContext,
    },
    href_pattern=PulpRepositoryContext.HREF_PATTERN,
    help=_(
        "Source repository to copy content from in the form `[[<plugin>:]<resource_type>:]<name>' "
        "or by href."
    ),
    required=True,
)


version_option = click.option(
    "--version", help=_("Version of the source repository to use"), type=int
)

remote_option = resource_option(
    "--remote",
    default_plugin="container",
    default_type="container",
    context_table={"container:container": PulpContainerRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_("Remote used for syncing in the form '[[<plugin>:]<resource_type>:]<name>' or by href."),
)


@pulp_group()
@type_option(
    choices={
        "container": PulpContainerRepositoryContext,
        "push": PulpContainerPushRepositoryContext,
    },
    default="container",
)
def repository() -> None:
    pass


lookup_options = [href_option, name_option, repository_lookup_option]
nested_lookup_options = [repository_href_option, repository_lookup_option]
update_options = [
    click.option("--description"),
    remote_option,
    retained_versions_option,
    pulp_labels_option,
]
create_options = update_options + [click.option("--name", required=True)]
contexts = {
    "tag": PulpContainerTagContext,
    "manifest": PulpContainerManifestContext,
    "blob": PulpContainerBlobContext,
}
container_context = (PulpContainerRepositoryContext,)
push_container_context = (PulpContainerPushRepositoryContext,)

repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(
    create_command(decorators=create_options, allowed_with_contexts=container_context)
)
repository.add_command(
    update_command(
        decorators=lookup_options + update_options, allowed_with_contexts=container_context
    )
)
repository.add_command(
    destroy_command(decorators=lookup_options, allowed_with_contexts=container_context)
)
repository.add_command(task_command(decorators=nested_lookup_options))
repository.add_command(version_command(decorators=nested_lookup_options))
repository.add_command(role_command(decorators=lookup_options))
repository.add_command(label_command(decorators=nested_lookup_options))
repository.add_command(
    repository_content_command(
        contexts=contexts,
        add_decorators=show_options,
        remove_decorators=show_options,
        allowed_with_contexts=container_context,
    )
)


@repository.command(allowed_with_contexts=container_context)
@name_option
@href_option
@repository_lookup_option
@remote_option
@pass_repository_context
def sync(
    repository_ctx: PulpRepositoryContext,
    remote: EntityFieldDefinition,
) -> None:
    """
    Sync the repository from a remote source.
    If remote is not specified sync will try to use the default remote associated with
    the repository
    """
    if not repository_ctx.capable("sync"):
        raise click.ClickException(_("Repository type does not support sync."))

    repository = repository_ctx.entity
    body: Dict[str, Any] = {}

    if remote:
        body["remote"] = remote
    elif repository["remote"] is None:
        raise click.ClickException(
            _(
                "Repository '{name}' does not have a default remote. "
                "Please specify with '--remote'."
            ).format(name=repository["name"])
        )

    repository_ctx.sync(body=body)


@repository.command(name="tag")
@name_option
@href_option
@repository_lookup_option
@click.option("--tag", help=_("Name to tag an image with"), required=True, callback=_tag_callback)
@click.option("--digest", help=_("SHA256 digest of the Manifest file"), required=True)
@pass_repository_context
def add_tag(
    repository_ctx: PulpContainerBaseRepositoryContext,
    digest: str,
    tag: str,
) -> None:
    digest = digest.strip()
    if not digest.startswith("sha256:"):
        digest = f"sha256:{digest}"
    if len(digest) != 71:  # len("sha256:") + 64
        raise click.ClickException("Improper SHA256, please provide a valid 64 digit digest.")

    repository_ctx.tag(tag, digest)


@repository.command(name="untag")
@name_option
@href_option
@repository_lookup_option
@click.option("--tag", help=_("Name of tag to remove"), required=True, callback=_tag_callback)
@pass_repository_context
def remove_tag(repository_ctx: PulpContainerBaseRepositoryContext, tag: str) -> None:
    repository_ctx.untag(tag)


@repository.command(allowed_with_contexts=container_context)
@name_option
@href_option
@repository_lookup_option
@source_option
@version_option
@click.option(
    "--tag",
    "tags",
    help=_("Multiple option of tag names to copy, leave blank to copy all"),
    multiple=True,
)
@pass_repository_context
def copy_tag(
    repository_ctx: PulpContainerRepositoryContext,
    source: PulpRepositoryContext,
    version: Optional[int],
    tags: List[str],
) -> None:
    href = source.entity["latest_version_href"]
    if version is not None:
        latest_version = int(href.split("/")[-2])
        if not (0 < int(version) <= latest_version):
            raise click.ClickException(
                _("Please specify a version that between 0 and the latest version {}").format(
                    latest_version
                )
            )
        href = f"{source.entity['versions_href']}{version}/"

    repository_ctx.copy_tag(source_href=href, tags=tags or None)


@repository.command(allowed_with_contexts=container_context)
@name_option
@href_option
@repository_lookup_option
@source_option
@version_option
@click.option(
    "--digest",
    "digests",
    help=_("Multiple option of manifest digests to copy, leave blank to copy all"),
    multiple=True,
)
@click.option(
    "--media-type",
    "media_types",
    help=_("Multiple option of media-types to copy, leave blank to copy all types"),
    type=click.Choice(
        [
            "application/vnd.docker.distribution.manifest.v1+json",
            "application/vnd.docker.distribution.manifest.v2+json",
            "application/vnd.docker.distribution.manifest.list.v2+json",
            "application/vnd.oci.image.manifest.v1+json",
            "application/vnd.oci.image.index.v1+json",
        ]
    ),
    multiple=True,
)
@pass_repository_context
def copy_manifest(
    repository_ctx: PulpContainerRepositoryContext,
    source: PulpRepositoryContext,
    version: Optional[int],
    digests: List[str],
    media_types: List[str],
) -> None:
    href = source.entity["latest_version_href"]
    if version is not None:
        latest_version = int(href.split("/")[-2])
        if not (0 < int(version) <= latest_version):
            raise click.ClickException(
                _("Please specify a version that between 0 and the latest version {}").format(
                    latest_version
                )
            )
        href = f"{source.entity['versions_href']}{version}/"

    repository_ctx.copy_manifest(
        source_href=href,
        digests=digests or None,
        media_types=media_types or None,
    )


def upload_file(pulp_ctx: PulpContext, file_location: str) -> str:
    try:
        with click.open_file(file_location, "rb") as fp:
            artifact_ctx = PulpArtifactContext(pulp_ctx)
            artifact_href = artifact_ctx.upload(fp)
    except OSError:
        raise click.ClickException(
            _("Failed to load content from {file}").format(file=file_location)
        )
    click.echo(_("Uploaded file: {}").format(artifact_href))
    return artifact_href  # type: ignore


@repository.command(allowed_with_contexts=container_context)
@name_option
@href_option
@click.option(
    "--containerfile",
    help=_(
        "An artifact href of an uploaded Containerfile. Can also be a local Containerfile to be"
        " uploaded using @."
    ),
    required=True,
)
@click.option("--tag", help=_("A tag name for the new image being built."))
@click.option(
    "--artifacts",
    help=_(
        "Directory of files to be uploaded and used during the build. Or a JSON string where each"
        " key is an artifact href and the value is it's relative path (name) inside the "
        "/pulp_working_directory of the build container executing the Containerfile."
    ),
    callback=_directory_or_json_callback,
)
@pass_repository_context
@pass_pulp_context
def build_image(
    pulp_ctx: PulpContext,
    repository_ctx: PulpContainerRepositoryContext,
    containerfile: str,
    tag: Optional[str],
    artifacts: Union[Dict[str, str], Path, None],
) -> None:
    if not repository_ctx.capable("build"):
        raise click.ClickException(_("Repository does not support image building."))

    container_artifact_href: str
    # Upload necessary files as artifacts if specified
    if containerfile[0] == "@":
        container_artifact_href = upload_file(pulp_ctx, containerfile[1:])
    else:
        artifact_ctx = PulpArtifactContext(pulp_ctx, pulp_href=containerfile)
        container_artifact_href = artifact_ctx.pulp_href

    if isinstance(artifacts, Path):
        artifacts_path = artifacts
        # Upload files in directory
        artifacts = {}
        for child in artifacts_path.rglob("*"):
            if child.is_file():
                artifact_href = upload_file(pulp_ctx, str(child))
                artifacts[artifact_href] = str(child.relative_to(artifacts_path))

    repository_ctx.build_image(container_artifact_href, tag, artifacts)


@repository.command(allowed_with_contexts=push_container_context)
@name_option
@href_option
@click.option("--digest", help=_("SHA256 digest of the Manifest file"), required=True)
@pass_repository_context
def remove_image(
    repository_ctx: PulpContainerPushRepositoryContext,
    digest: str,
) -> None:
    digest = digest.strip()
    if not digest.startswith("sha256:"):
        digest = f"sha256:{digest}"
    if len(digest) != 71:  # len("sha256:") + 64
        raise click.ClickException("Improper SHA256, please provide a valid 64 digit digest.")

    repository_ctx.remove_image(digest)
