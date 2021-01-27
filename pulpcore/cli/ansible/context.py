from pulpcore.cli.common.context import (
    PulpEntityContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)

# TODO Add Role and Collection Content contexts


class PulpAnsibleDistributionContext(PulpEntityContext):
    ENTITY = "distribution"
    HREF = "ansible_ansible_distribution_href"
    LIST_ID = "distributions_ansible_ansible_list"
    READ_ID = "distributions_ansible_ansible_read"
    CREATE_ID = "distributions_ansible_ansible_create"
    UPDATE_ID = "distributions_ansible_ansible_partial_update"
    DELETE_ID = "distributions_ansible_ansible_delete"


class PulpAnsibleRoleRemoteContext(PulpEntityContext):
    ENTITY = "role remote"
    HREF = "ansible_role_remote_href"
    LIST_ID = "remotes_ansible_role_list"
    READ_ID = "remotes_ansible_role_read"
    CREATE_ID = "remotes_ansible_role_create"
    UPDATE_ID = "remotes_ansible_role_partial_update"
    DELETE_ID = "remotes_ansible_role_delete"


class PulpAnsibleCollectionRemoteContext(PulpEntityContext):
    ENTITY = "collection remote"
    HREF = "ansible_collection_remote_href"
    LIST_ID = "remotes_ansible_collection_list"
    READ_ID = "remotes_ansible_collection_read"
    CREATE_ID = "remotes_ansible_collection_create"
    UPDATE_ID = "remotes_ansible_collection_partial_update"
    DELETE_ID = "remotes_ansible_collection_delete"


class PulpAnsibleRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "ansible_ansible_repository_version_href"
    REPOSITORY_HREF = "ansible_ansible_repository_href"
    LIST_ID = "repositories_ansible_ansible_versions_list"
    READ_ID = "repositories_ansible_ansible_versions_read"
    DELETE_ID = "repositories_ansible_ansible_versions_delete"
    REPAIR_ID = "repositories_ansible_ansible_versions_repair"


class PulpAnsibleRepositoryContext(PulpRepositoryContext):
    HREF = "ansible_ansible_repository_href"
    LIST_ID = "repositories_ansible_ansible_list"
    READ_ID = "repositories_ansible_ansible_read"
    CREATE_ID = "repositories_ansible_ansible_create"
    UPDATE_ID = "repositories_ansible_ansible_partial_update"
    DELETE_ID = "repositories_ansible_ansible_delete"
    SYNC_ID = "repositories_ansible_ansible_sync"
    MODIFY_ID = "repositories_ansible_ansible_modify"
    VERSION_CONTEXT = PulpAnsibleRepositoryVersionContext
