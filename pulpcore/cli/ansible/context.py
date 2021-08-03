import gettext

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


class PulpAnsibleCollectionVersionContext(PulpContentContext):
    ENTITY = "ansible collection version"
    ENTITIES = "ansible collection versions"
    HREF = "ansible_collection_version_href"
    LIST_ID = "content_ansible_collection_versions_list"
    READ_ID = "content_ansible_collection_versions_read"
    CREATE_ID = "content_ansible_collection_versions_create"


class PulpAnsibleRoleContext(PulpContentContext):
    ENTITY = "ansible role"
    ENTITIES = "ansible roles"
    HREF = "ansible_role_href"
    LIST_ID = "content_ansible_roles_list"
    READ_ID = "content_ansible_roles_read"
    CREATE_ID = "content_ansible_roles_create"


class PulpAnsibleDistributionContext(PulpEntityContext):
    ENTITY = "distribution"
    HREF = "ansible_ansible_distribution_href"
    LIST_ID = "distributions_ansible_ansible_list"
    READ_ID = "distributions_ansible_ansible_read"
    CREATE_ID = "distributions_ansible_ansible_create"
    UPDATE_ID = "distributions_ansible_ansible_partial_update"
    DELETE_ID = "distributions_ansible_ansible_delete"

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        body = super().preprocess_body(body)
        version = body.pop("version", None)
        if version is not None:
            repository_href = body.pop("repository")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        return body


class PulpAnsibleRoleRemoteContext(PulpRemoteContext):
    ENTITY = "role remote"
    HREF = "ansible_role_remote_href"
    LIST_ID = "remotes_ansible_role_list"
    READ_ID = "remotes_ansible_role_read"
    CREATE_ID = "remotes_ansible_role_create"
    UPDATE_ID = "remotes_ansible_role_partial_update"
    DELETE_ID = "remotes_ansible_role_delete"


class PulpAnsibleCollectionRemoteContext(PulpRemoteContext):
    ENTITY = "collection remote"
    HREF = "ansible_collection_remote_href"
    LIST_ID = "remotes_ansible_collection_list"
    READ_ID = "remotes_ansible_collection_read"
    CREATE_ID = "remotes_ansible_collection_create"
    UPDATE_ID = "remotes_ansible_collection_partial_update"
    DELETE_ID = "remotes_ansible_collection_delete"
    collection_nullable = ["auth_url", "requirements_file", "token"]

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        body = super().preprocess_body(body)
        if "requirements" in body.keys():
            body["requirements_file"] = body.pop("requirements")
        return body


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
    CAPABILITIES = {"pulpexport": [PluginRequirement("ansible", "0.7.0")]}


registered_repository_contexts["ansible:ansible"] = PulpAnsibleRepositoryContext
