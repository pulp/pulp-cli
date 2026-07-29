import typing as t

from pulp_glue.common.context import (
    EntityDefinition,
    PluginRequirement,
    PulpACSContext,
    PulpContentContext,
    PulpDistributionContext,
    PulpEntityContext,
    PulpPublicationContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    PulpViewSetContext,
    api_spec_quirk,
)
from pulp_glue.common.exceptions import PulpException
from pulp_glue.common.i18n import get_translation

translation = get_translation(__package__)
_ = translation.gettext


@api_spec_quirk(PluginRequirement("rpm"))  # TODO fix this upstream and add the version here.
def patch_rpm_copy_scheme(api_spec: t.Any) -> t.Any:
    path, operation = next(
        ((k, v["post"]) for k, v in api_spec["paths"].items() if k.endswith("/rpm/copy/"))
    )
    api_spec["components"]["schemas"]["RpmCopy"] = {
        "type": "object",
        "description": "A serializer for Content Copy API.",
        "properties": {
            "config": {
                "description": "A JSON document describing sources, destinations,"
                " and content to be copied"
            },
            "dependency_solving": {"type": "boolean"},
        },
        "required": ["config"],
    }
    operation["operationId"] = "rpm_copy_content"
    for item in operation["requestBody"]["content"].values():
        item["schema"]["$ref"] = "#/components/schemas/RpmCopy"

    return api_spec


class PulpRpmACSContext(PulpACSContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "rpm"
    ENTITY = _("rpm ACS")
    ENTITIES = _("rpm ACSes")
    HREF = "rpm_rpm_alternate_content_source_href"
    ID_PREFIX = "acs_rpm_rpm"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]
    CAPABILITIES = {"roles": []}


class PulpRpmCompsXmlContext(PulpEntityContext):
    UPLOAD_COMPS_ID: t.ClassVar[str] = "rpm_comps_upload"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]

    def upload_comps(self, file: t.IO[bytes], repo_href: str | None, replace: bool | None) -> t.Any:
        self.pulp_ctx.echo(_("Uploading file {filename}").format(filename=file.name), err=True)
        file.seek(0)
        return self.call(
            "upload_comps",
            body={"repository": repo_href, "replace": replace, "file": file},
        )


class PulpRpmDistributionContext(PulpDistributionContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "rpm"
    ENTITY = _("rpm distribution")
    ENTITIES = _("rpm distributions")
    HREF = "rpm_rpm_distribution_href"
    ID_PREFIX = "distributions_rpm_rpm"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]
    CAPABILITIES = {"roles": []}

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if "repository" in body and "publication" not in body:
            body["publication"] = None
        if "repository" not in body and "publication" in body:
            body["repository"] = None

        version = body.pop("version", None)
        if version is not None:
            self.pulp_ctx.needs_plugin(PluginRequirement("core", specifier=">=3.106.0"))
            repository_href = body.pop("repository", None)
            if repository_href is None and partial:
                repository_href = self.entity.get("repository")
            if repository_href is None:
                raise PulpException(_("--repository must be provided"))
            body["repository_version"] = f"{repository_href}versions/{version}/"
            body["repository"] = None
            body["publication"] = None
        elif "repository" in body and self.pulp_ctx.has_plugin(
            PluginRequirement("core", specifier=">=3.106.0")
        ):
            body["repository_version"] = None

        return body


class PulpRpmPackageContext(PulpContentContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "package"
    ENTITY = "rpm package"
    ENTITIES = "rpm packages"
    HREF = "rpm_package_href"
    ID_PREFIX = "content_rpm_packages"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]
    CAPABILITIES = {"upload": []}

    def upload(
        self,
        file: t.IO[bytes],
        chunk_size: int | None,
        repository: PulpRepositoryContext | None,
        **kwargs: t.Any,
    ) -> t.Any:
        """
        Create an RPM package by uploading a file.

        This function is deprecated. The create call can handle the upload logic transparently.

        Parameters:
            file: A file like object that supports `os.path.getsize`.
            chunk_size: Size of the chunks to upload independently. `None` to disable chunking.
            repository: Repository context to add the newly created content to.
            kwargs: Extra args specific to the content type, passed to the create call.

        Returns:
            The result of the create task.
        """
        self.needs_capability("upload")
        body: dict[str, t.Any] = {**kwargs}

        self._prepare_upload(body, file, chunk_size)

        if repository is None and self.pulp_ctx.has_plugin(
            PluginRequirement("rpm", specifier=">=3.32.5")
        ):
            # "Synchronous upload"
            return self.call("upload", body=body)

        if repository is not None:
            body["repository"] = repository
        return self.create(body=body)


class PulpRpmAdvisoryContext(PulpContentContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "update_record"
    ENTITY = "rpm advisory"
    ENTITIES = "rpm advisories"
    HREF = "rpm_update_record_href"
    ID_PREFIX = "content_rpm_advisories"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]


class PulpRpmDistributionTreeContext(PulpContentContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "distribution_tree"
    ENTITY = "rpm distribution tree"
    ENTITIES = "rpm distribution trees"
    HREF = "rpm_distribution_tree_href"
    ID_PREFIX = "content_rpm_distribution_trees"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]


class PulpRpmModulemdDefaultsContext(PulpContentContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "modulemd_defaults"
    ENTITY = "rpm modulemd defaults"
    ENTITIES = "rpm modulemd defaults"
    HREF = "rpm_modulemd_defaults_href"
    ID_PREFIX = "content_rpm_modulemd_defaults"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]


class PulpRpmModulemdContext(PulpContentContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "modulemd"
    ENTITY = "rpm modulemd"
    ENTITIES = "rpm modulemds"
    HREF = "rpm_modulemd_href"
    ID_PREFIX = "content_rpm_modulemds"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]


class PulpRpmPackageCategoryContext(PulpContentContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "package_category"
    ENTITY = "rpm package category"
    ENTITIES = "rpm package categories"
    HREF = "rpm_package_category_href"
    ID_PREFIX = "content_rpm_packagecategories"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]


class PulpRpmPackageEnvironmentContext(PulpContentContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "package_environment"
    ENTITY = "rpm package environment"
    ENTITIES = "rpm package environments"
    HREF = "rpm_package_environment_href"
    ID_PREFIX = "content_rpm_packageenvironments"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]


class PulpRpmPackageGroupContext(PulpContentContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "package_group"
    ENTITY = "rpm package group"
    ENTITIES = "rpm package groups"
    HREF = "rpm_package_group_href"
    ID_PREFIX = "content_rpm_packagegroups"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]


class PulpRpmPackageLangpacksContext(PulpContentContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "package_langpack"
    ENTITY = "rpm package langpack"
    ENTITIES = "rpm package langpacks"
    HREF = "rpm_package_langpacks_href"
    ID_PREFIX = "content_rpm_packagelangpacks"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]


class PulpRpmRepoMetadataFileContext(PulpContentContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "repo_metadata_file"
    ENTITY = "rpm repo metadata file"
    ENTITIES = "rpm repo metadata files"
    HREF = "rpm_repo_metadata_file_href"
    ID_PREFIX = "content_rpm_repo_metadata_files"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]


class PulpRpmPublicationContext(PulpPublicationContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "rpm"
    ENTITY = _("rpm publication")
    ENTITIES = _("rpm publications")
    HREF = "rpm_rpm_publication_href"
    ID_PREFIX = "publications_rpm_rpm"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]
    CAPABILITIES = {"roles": []}

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        version = body.pop("version", None)
        if version is not None:
            repository_href = body.pop("repository")
            body["repository_version"] = f"{repository_href}versions/{version}/"

        if "metadata_checksum_type" in body or "package_checksum_type" in body:
            self.pulp_ctx.needs_plugin(
                PluginRequirement(
                    "rpm",
                    specifier=">=3.30.0",
                    inverted=True,
                    feature=_("package_checksum_type/metadata_checksum_type"),
                )
            )

        if "repo_gpgcheck" in body or "gpgcheck" in body:
            self.pulp_ctx.needs_plugin(
                PluginRequirement(
                    "rpm",
                    specifier=">=3.30.0",
                    inverted=True,
                    feature=_("gpgcheck/repo_gpgcheck"),
                )
            )

        return body


class PulpRpmRemoteContext(PulpRemoteContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "rpm"
    ENTITY = _("rpm remote")
    ENTITIES = _("rpm remotes")
    HREF = "rpm_rpm_remote_href"
    ID_PREFIX = "remotes_rpm_rpm"
    NULLABLES = PulpRemoteContext.NULLABLES | {"sles_auth_token"}
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]
    CAPABILITIES = {"roles": []}


class PulpUlnRemoteContext(PulpRemoteContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "uln"
    ENTITY = _("uln remote")
    ENTITIES = _("uln remotes")
    HREF = "rpm_uln_remote_href"
    ID_PREFIX = "remotes_rpm_uln"
    NULLABLES = PulpRemoteContext.NULLABLES | {"uln-server-base-url"}
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]
    CAPABILITIES = {"roles": []}


class PulpRpmRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "rpm_rpm_repository_version_href"
    ID_PREFIX = "repositories_rpm_rpm_versions"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]
    CAPABILITIES = {"scan": [PluginRequirement("rpm", specifier=">=3.38.0")]}


class PulpRpmRepositoryContext(PulpRepositoryContext):
    PLUGIN = "rpm"
    RESOURCE_TYPE = "rpm"
    HREF = "rpm_rpm_repository_href"
    ID_PREFIX = "repositories_rpm_rpm"
    ENTITY = _("rpm repository")
    ENTITIES = _("rpm repositories")
    VERSION_CONTEXT = PulpRpmRepositoryVersionContext
    CAPABILITIES = {
        "sync": [],
        "pulpexport": [],
        "roles": [],
    }
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]
    NULLABLES = PulpRepositoryContext.NULLABLES | {"osv_config"}

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if "metadata_checksum_type" in body or "package_checksum_type" in body:
            self.pulp_ctx.needs_plugin(
                PluginRequirement(
                    "rpm",
                    specifier=">=3.30.0",
                    inverted=True,
                    feature=_("package_checksum_type/metadata_checksum_type"),
                )
            )
        if "repo_gpgcheck" in body or "gpgcheck" in body:
            self.pulp_ctx.needs_plugin(
                PluginRequirement(
                    "rpm",
                    specifier=">=3.30.0",
                    inverted=True,
                    feature=_("gpgcheck/repo_gpgcheck"),
                )
            )

        return body


class PulpRpmPruneContext(PulpViewSetContext):
    ID_PREFIX: t.ClassVar[str] = "rpm_prune"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.27.0")]

    def prune_packages(
        self,
        repo_hrefs: list[str | PulpRpmRepositoryContext],
        keep_days: int | None,
        dry_run: bool | None,
    ) -> t.Any:
        body: dict[str, t.Any] = {
            "repo_hrefs": repo_hrefs,
            "keep_days": keep_days,
            "dry_run": dry_run,
        }
        return self.call("prune_packages", body=body)


class PulpRpmCopyContext(PulpViewSetContext):
    COPY_ID: t.ClassVar[str] = "rpm_copy_content"
    NEEDS_PLUGINS = [PluginRequirement("rpm", specifier=">=3.26.0")]

    def copy(
        self,
        config: list[dict[str, t.Any]],
        dependency_solving: bool | None = False,
    ) -> t.Any:
        body: dict[str, t.Any] = {
            "config": config,
            "dependency_solving": dependency_solving,
        }
        return self.call("copy", body=body)
