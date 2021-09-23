import gettext
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

_ = gettext.gettext


class PulpRpmACSContext(PulpEntityContext):
    ENTITY = _("rpm ACS")
    ENTITIES = _("rpm ACSes")
    HREF = "rpm_rpm_alternate_content_source_href"
    LIST_ID = "acs_rpm_rpm_list"
    READ_ID = "acs_rpm_rpm_read"
    CREATE_ID = "acs_rpm_rpm_create"
    UPDATE_ID = "acs_rpm_rpm_partial_update"
    DELETE_ID = "acs_rpm_rpm_delete"
    REFRESH_ID = "acs_rpm_rpm_refresh"

    def refresh(self, href: str) -> Any:
        return self.pulp_ctx.call(
            self.REFRESH_ID,
            parameters={self.HREF: href},
        )


class PulpRpmDistributionContext(PulpEntityContext):
    ENTITY = _("rpm distribution")
    ENTITIES = _("rpm distributions")
    HREF = "rpm_rpm_distribution_href"
    LIST_ID = "distributions_rpm_rpm_list"
    READ_ID = "distributions_rpm_rpm_read"
    CREATE_ID = "distributions_rpm_rpm_create"
    UPDATE_ID = "distributions_rpm_rpm_partial_update"
    DELETE_ID = "distributions_rpm_rpm_delete"
    NULLABLES = {"publication"}


class PulpRpmPackageContext(PulpContentContext):
    ENTITY = "rpm package"
    ENTITIES = "rpm packages"
    HREF = "rpm_package_href"
    LIST_ID = "content_rpm_packages_list"
    READ_ID = "content_rpm_packages_read"
    CREATE_ID = "content_rpm_packages_create"


class PulpRpmPublicationContext(PulpEntityContext):
    ENTITY = _("rpm publication")
    ENTITIES = _("rpm publications")
    HREF = "rpm_rpm_publication_href"
    LIST_ID = "publications_rpm_rpm_list"
    READ_ID = "publications_rpm_rpm_read"
    CREATE_ID = "publications_rpm_rpm_create"
    DELETE_ID = "publications_rpm_rpm_delete"

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        body = super().preprocess_body(body)
        version = body.pop("version", None)
        if version is not None:
            repository_href = body.pop("repository")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        return body


class PulpRpmRemoteContext(PulpRemoteContext):
    ENTITY = _("rpm remote")
    ENTITIES = _("rpm remotes")
    HREF = "rpm_rpm_remote_href"
    LIST_ID = "remotes_rpm_rpm_list"
    READ_ID = "remotes_rpm_rpm_read"
    CREATE_ID = "remotes_rpm_rpm_create"
    UPDATE_ID = "remotes_rpm_rpm_partial_update"
    DELETE_ID = "remotes_rpm_rpm_delete"
    NULLABLES = {
        "ca_cert",
        "client_cert",
        "client_key",
        "username",
        "password",
        "proxy_url",
        "proxy_username",
        "proxy_password",
        "sles_auth_token",
    }


class PulpRpmRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "rpm_rpm_repository_version_href"
    REPOSITORY_HREF = "rpm_rpm_repository_href"
    LIST_ID = "repositories_rpm_rpm_versions_list"
    READ_ID = "repositories_rpm_rpm_versions_read"
    DELETE_ID = "repositories_rpm_rpm_versions_delete"
    REPAIR_ID = "repositories_rpm_rpm_versions_repair"


class PulpRpmRepositoryContext(PulpRepositoryContext):
    HREF = "rpm_rpm_repository_href"
    LIST_ID = "repositories_rpm_rpm_list"
    READ_ID = "repositories_rpm_rpm_read"
    CREATE_ID = "repositories_rpm_rpm_create"
    UPDATE_ID = "repositories_rpm_rpm_partial_update"
    DELETE_ID = "repositories_rpm_rpm_delete"
    SYNC_ID = "repositories_rpm_rpm_sync"
    MODIFY_ID = "repositories_rpm_rpm_modify"
    VERSION_CONTEXT = PulpRpmRepositoryVersionContext
    CAPABILITIES = {"pulpexport": [PluginRequirement("rpm")]}


registered_repository_contexts["rpm:rpm"] = PulpRpmRepositoryContext
