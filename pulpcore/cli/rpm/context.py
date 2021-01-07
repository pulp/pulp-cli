from pulpcore.cli.common.context import (
    PulpEntityContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)


class PulpRpmDistributionContext(PulpEntityContext):
    ENTITY = "distribution"
    HREF = "rpm_rpm_distribution_href"
    LIST_ID = "distributions_rpm_rpm_list"
    READ_ID = "distributions_rpm_rpm_read"
    CREATE_ID = "distributions_rpm_rpm_create"
    UPDATE_ID = "distributions_rpm_rpm_update"
    DELETE_ID = "distributions_rpm_rpm_delete"


class PulpRpmPublicationContext(PulpEntityContext):
    ENTITY = "publication"
    HREF = "rpm_rpm_publication_href"
    LIST_ID = "publications_rpm_rpm_list"
    READ_ID = "publications_rpm_rpm_read"
    CREATE_ID = "publications_rpm_rpm_create"
    DELETE_ID = "publications_rpm_rpm_delete"


class PulpRpmRemoteContext(PulpEntityContext):
    ENTITY = "remote"
    HREF = "rpm_rpm_remote_href"
    LIST_ID = "remotes_rpm_rpm_list"
    CREATE_ID = "remotes_rpm_rpm_create"
    UPDATE_ID = "remotes_rpm_rpm_update"
    DELETE_ID = "remotes_rpm_rpm_delete"


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
    UPDATE_ID = "repositories_rpm_rpm_update"
    DELETE_ID = "repositories_rpm_rpm_delete"
    SYNC_ID = "repositories_rpm_rpm_sync"
    VERSION_CONTEXT = PulpRpmRepositoryVersionContext
