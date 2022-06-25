from typing import Any

from pulpcore.cli.common.context import (
    EntityDefinition,
    PluginRequirement,
    PulpContentContext,
    PulpEntityContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    registered_repository_contexts,
)
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


class PulpFileACSContext(PulpEntityContext):
    ENTITY = _("file ACS")
    ENTITIES = _("file ACSes")
    HREF = "file_file_alternate_content_source_href"
    ID_PREFIX = "acs_file_file"
    CAPABILITIES = {"roles": [PluginRequirement("file", min="1.11.0")]}

    def refresh(self, href: str) -> Any:
        return self.call("refresh", parameters={self.HREF: href})


class PulpFileContentContext(PulpContentContext):
    ENTITY = _("file content")
    ENTITIES = _("file content")
    HREF = "file_file_content_href"
    ID_PREFIX = "content_file_files"


class PulpFileDistributionContext(PulpEntityContext):
    ENTITY = _("file distribution")
    ENTITIES = _("file distributions")
    HREF = "file_file_distribution_href"
    ID_PREFIX = "distributions_file_file"
    NULLABLES = {"publication", "repository"}
    CAPABILITIES = {"roles": [PluginRequirement("file", min="1.11.0")]}

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        body = super().preprocess_body(body)
        if self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.16.0")):
            if "repository" in body and "publication" not in body:
                body["publication"] = None
            if "repository" not in body and "publication" in body:
                body["repository"] = None
        return body


class PulpFilePublicationContext(PulpEntityContext):
    ENTITY = _("file publication")
    ENTITIES = _("file publications")
    HREF = "file_file_publication_href"
    ID_PREFIX = "publications_file_file"
    CAPABILITIES = {"roles": [PluginRequirement("file", min="1.11.0")]}

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        body = super().preprocess_body(body)
        version = body.pop("version", None)
        if version is not None:
            repository_href = body.pop("repository")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        return body


class PulpFileRemoteContext(PulpRemoteContext):
    ENTITY = _("file remote")
    ENTITIES = _("file remotes")
    HREF = "file_file_remote_href"
    ID_PREFIX = "remotes_file_file"
    CAPABILITIES = {"roles": [PluginRequirement("file", min="1.11.0")]}


class PulpFileRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "file_file_repository_version_href"
    ID_PREFIX = "repositories_file_file_versions"


class PulpFileRepositoryContext(PulpRepositoryContext):
    HREF = "file_file_repository_href"
    ID_PREFIX = "repositories_file_file"
    VERSION_CONTEXT = PulpFileRepositoryVersionContext
    CAPABILITIES = {
        "pulpexport": [PluginRequirement("file")],
        "roles": [PluginRequirement("file", min="1.11.0")],
    }


registered_repository_contexts["file:file"] = PulpFileRepositoryContext
