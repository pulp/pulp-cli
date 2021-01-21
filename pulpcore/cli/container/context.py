from pulpcore.cli.common.context import (
    PulpEntityContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)


class PulpContainerDistributionContext(PulpEntityContext):
    ENTITY = "distribution"
    HREF = "container_container_distribution_href"
    LIST_ID = "distributions_container_container_list"
    READ_ID = "distributions_container_container_read"
    CREATE_ID = "distributions_container_container_create"
    UPDATE_ID = "distributions_container_container_partial_update"
    DELETE_ID = "distributions_container_container_delete"


class PulpContainerRemoteContext(PulpEntityContext):
    ENTITY = "remote"
    HREF = "container_container_remote_href"
    LIST_ID = "remotes_container_container_list"
    CREATE_ID = "remotes_container_container_create"
    UPDATE_ID = "remotes_container_container_partial_update"
    DELETE_ID = "remotes_container_container_delete"


class PulpContainerRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "container_container_repository_version_href"
    REPOSITORY_HREF = "container_container_repository_href"
    LIST_ID = "repositories_container_container_versions_list"
    READ_ID = "repositories_container_container_versions_read"
    DELETE_ID = "repositories_container_container_versions_delete"


class PulpContainerPushRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "container_container_push_repository_version_href"
    REPOSITORY_HREF = "container_container_push_repository_href"
    LIST_ID = "repositories_container_container_push_versions_list"
    READ_ID = "repositories_container_container_push_versions_read"
    DELETE_ID = "repositories_container_container_push_versions_delete"


class PulpContainerRepositoryContext(PulpRepositoryContext):
    HREF = "container_container_repository_href"
    LIST_ID = "repositories_container_container_list"
    READ_ID = "repositories_container_container_read"
    CREATE_ID = "repositories_container_container_create"
    UPDATE_ID = "repositories_container_container_partial_update"
    DELETE_ID = "repositories_container_container_delete"
    SYNC_ID = "repositories_container_container_sync"
    VERSION_CONTEXT = PulpContainerRepositoryVersionContext


class PulpContainerPushRepositoryContext(PulpRepositoryContext):
    HREF = "container_container_push_repository_href"
    LIST_ID = "repositories_container_container_push_list"
    READ_ID = "repositories_container_container_push_read"
    # CREATE_ID = "repositories_container_container_push_create"
    # UPDATE_ID = "repositories_container_container_push_update"
    # DELETE_ID = "repositories_container_container_push_delete"
    # Cannot sync a push type repository
    # TODO Incorporate into capabilities
    # SYNC_ID = "repositories_container_container_push_sync"
    VERSION_CONTEXT = PulpContainerPushRepositoryVersionContext
