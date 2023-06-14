from typing import Any, Mapping, Optional

from pulp_glue.common.context import (
    EntityDefinition,
    PluginRequirement,
    PulpACSContext,
    PulpContentContext,
    PulpDistributionContext,
    PulpPublicationContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpArtifactContext

translation = get_translation(__name__)
_ = translation.gettext


class PulpFileACSContext(PulpACSContext):
    PLUGIN = "file"
    RESOURCE_TYPE = "file"
    ENTITY = _("file ACS")
    ENTITIES = _("file ACSes")
    HREF = "file_file_alternate_content_source_href"
    ID_PREFIX = "acs_file_file"
    NEEDS_PLUGINS = [PluginRequirement("file", specifier=">=1.9.0")]
    CAPABILITIES = {"roles": [PluginRequirement("file", specifier=">=1.11.0")]}


class PulpFileContentContext(PulpContentContext):
    PLUGIN = "file"
    RESOURCE_TYPE = "file"
    ENTITY = _("file content")
    ENTITIES = _("file content")
    HREF = "file_file_content_href"
    ID_PREFIX = "content_file_files"
    NEEDS_PLUGINS = [PluginRequirement("file", specifier=">=1.6.0")]
    CAPABILITIES = {"upload": []}

    def create(
        self,
        body: EntityDefinition,
        parameters: Optional[Mapping[str, Any]] = None,
        non_blocking: bool = False,
    ) -> Any:
        if "sha256" in body:
            body = body.copy()
            body["artifact"] = PulpArtifactContext(
                self.pulp_ctx, entity={"sha256": body.pop("sha256")}
            )
        return super().create(body=body, parameters=parameters, non_blocking=non_blocking)


class PulpFileDistributionContext(PulpDistributionContext):
    PLUGIN = "file"
    RESOURCE_TYPE = "file"
    ENTITY = _("file distribution")
    ENTITIES = _("file distributions")
    HREF = "file_file_distribution_href"
    ID_PREFIX = "distributions_file_file"
    CAPABILITIES = {"roles": [PluginRequirement("file", specifier=">=1.11.0")]}
    NEEDS_PLUGINS = [PluginRequirement("file", specifier=">=1.6.0")]

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if self.pulp_ctx.has_plugin(PluginRequirement("core", specifier=">=3.16.0")):
            if "repository" in body and "publication" not in body:
                body["publication"] = None
            if "repository" not in body and "publication" in body:
                body["repository"] = None
        return body


class PulpFilePublicationContext(PulpPublicationContext):
    PLUGIN = "file"
    RESOURCE_TYPE = "file"
    ENTITY = _("file publication")
    ENTITIES = _("file publications")
    HREF = "file_file_publication_href"
    ID_PREFIX = "publications_file_file"
    CAPABILITIES = {"roles": [PluginRequirement("file", specifier=">=1.11.0")]}
    NULLABLES = {"manifest"}
    NEEDS_PLUGINS = [PluginRequirement("file", specifier=">=1.6.0")]

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        version = body.pop("version", None)
        if version is not None:
            repository_href = body.pop("repository")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        return body


class PulpFileRemoteContext(PulpRemoteContext):
    PLUGIN = "file"
    RESOURCE_TYPE = "file"
    ENTITY = _("file remote")
    ENTITIES = _("file remotes")
    HREF = "file_file_remote_href"
    ID_PREFIX = "remotes_file_file"
    CAPABILITIES = {"roles": [PluginRequirement("file", specifier=">=1.11.0")]}
    NEEDS_PLUGINS = [PluginRequirement("file", specifier=">=1.6.0")]


class PulpFileRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "file_file_repository_version_href"
    ID_PREFIX = "repositories_file_file_versions"
    NEEDS_PLUGINS = [PluginRequirement("file", specifier=">=1.6.0")]


class PulpFileRepositoryContext(PulpRepositoryContext):
    PLUGIN = "file"
    RESOURCE_TYPE = "file"
    HREF = "file_file_repository_href"
    ENTITY = _("file repository")
    ENTITIES = _("file repositories")
    ID_PREFIX = "repositories_file_file"
    VERSION_CONTEXT = PulpFileRepositoryVersionContext
    CAPABILITIES = {
        "sync": [PluginRequirement("file")],
        "pulpexport": [PluginRequirement("file")],
        "roles": [PluginRequirement("file", specifier=">=1.11.0")],
    }
    NULLABLES = PulpRepositoryContext.NULLABLES.union({"manifest"})
    NEEDS_PLUGINS = [PluginRequirement("file", specifier=">=1.6.0")]

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if "autopublish" in body:
            self.pulp_ctx.needs_plugin(PluginRequirement("file", specifier=">=1.7.0"))
        return body
