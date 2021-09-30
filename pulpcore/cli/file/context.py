import gettext
from typing import Any, ClassVar

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

_ = gettext.gettext


class PulpFileACSContext(PulpEntityContext):
    ENTITY = _("file ACS")
    ENTITIES = _("file ACSes")
    HREF = "file_file_alternate_content_source_href"
    LIST_ID = "acs_file_file_list"
    READ_ID = "acs_file_file_read"
    CREATE_ID = "acs_file_file_create"
    UPDATE_ID = "acs_file_file_partial_update"
    DELETE_ID = "acs_file_file_delete"
    REFRESH_ID: ClassVar[str] = "acs_file_file_refresh"

    def refresh(self, href: str) -> Any:
        return self.pulp_ctx.call(
            self.REFRESH_ID,
            parameters={self.HREF: href},
        )


class PulpFileContentContext(PulpContentContext):
    ENTITY = _("file content")
    ENTITIES = _("file content")
    HREF = "file_file_content_href"
    LIST_ID = "content_file_files_list"
    READ_ID = "content_file_files_read"
    CREATE_ID = "content_file_files_create"


class PulpFileDistributionContext(PulpEntityContext):
    ENTITY = _("file distribution")
    ENTITIES = _("file distributions")
    HREF = "file_file_distribution_href"
    LIST_ID = "distributions_file_file_list"
    READ_ID = "distributions_file_file_read"
    CREATE_ID = "distributions_file_file_create"
    UPDATE_ID = "distributions_file_file_partial_update"
    DELETE_ID = "distributions_file_file_delete"
    NULLABLES = {"publication"}


class PulpFilePublicationContext(PulpEntityContext):
    ENTITY = _("file publication")
    ENTITIES = _("file publications")
    HREF = "file_file_publication_href"
    LIST_ID = "publications_file_file_list"
    READ_ID = "publications_file_file_read"
    CREATE_ID = "publications_file_file_create"
    DELETE_ID = "publications_file_file_delete"

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
    LIST_ID = "remotes_file_file_list"
    CREATE_ID = "remotes_file_file_create"
    READ_ID = "remotes_file_file_read"
    UPDATE_ID = "remotes_file_file_partial_update"
    DELETE_ID = "remotes_file_file_delete"


class PulpFileRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "file_file_repository_version_href"
    REPOSITORY_HREF = "file_file_repository_href"
    LIST_ID = "repositories_file_file_versions_list"
    READ_ID = "repositories_file_file_versions_read"
    DELETE_ID = "repositories_file_file_versions_delete"
    REPAIR_ID = "repositories_file_file_versions_repair"


class PulpFileRepositoryContext(PulpRepositoryContext):
    HREF = "file_file_repository_href"
    LIST_ID = "repositories_file_file_list"
    READ_ID = "repositories_file_file_read"
    CREATE_ID = "repositories_file_file_create"
    UPDATE_ID = "repositories_file_file_partial_update"
    DELETE_ID = "repositories_file_file_delete"
    SYNC_ID = "repositories_file_file_sync"
    MODIFY_ID = "repositories_file_file_modify"
    VERSION_CONTEXT = PulpFileRepositoryVersionContext
    CAPABILITIES = {"pulpexport": [PluginRequirement("file")]}


registered_repository_contexts["file:file"] = PulpFileRepositoryContext
