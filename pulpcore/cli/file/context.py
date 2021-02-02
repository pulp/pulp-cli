from pulpcore.cli.common.context import (
    PulpEntityContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)


class PulpFileContentContext(PulpEntityContext):
    ENTITY = "file content"
    ENTITIES = "file content"
    HREF = "file_file_content_href"
    LIST_ID = "content_file_files_list"
    READ_ID = "content_file_files_read"
    CREATE_ID = "content_file_files_create"


class PulpFileDistributionContext(PulpEntityContext):
    ENTITY = "file distribution"
    ENTITIES = "file distributions"
    HREF = "file_file_distribution_href"
    LIST_ID = "distributions_file_file_list"
    READ_ID = "distributions_file_file_read"
    CREATE_ID = "distributions_file_file_create"
    UPDATE_ID = "distributions_file_file_partial_update"
    DELETE_ID = "distributions_file_file_delete"


class PulpFilePublicationContext(PulpEntityContext):
    ENTITY = "file publication"
    ENTITIES = "file publications"
    HREF = "file_file_publication_href"
    LIST_ID = "publications_file_file_list"
    READ_ID = "publications_file_file_read"
    CREATE_ID = "publications_file_file_create"
    DELETE_ID = "publications_file_file_delete"


class PulpFileRemoteContext(PulpEntityContext):
    ENTITY = "file remote"
    ENTITIES = "file remotes"
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
