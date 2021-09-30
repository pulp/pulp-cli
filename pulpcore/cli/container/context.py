import gettext

from pulpcore.cli.common.context import (
    EntityDefinition,
    PluginRequirement,
    PulpEntityContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    registered_repository_contexts,
)

_ = gettext.gettext


class PulpContainerNamespaceContext(PulpEntityContext):
    ENTITY = _("container namespace")
    ENTITIES = _("container namespaces")
    HREF = "container_container_namespace_href"
    LIST_ID = "pulp_container_namespaces_list"
    READ_ID = "pulp_container_namespaces_read"
    CREATE_ID = "pulp_container_namespaces_create"
    DELETE_ID = "pulp_container_namespaces_delete"


class PulpContainerDistributionContext(PulpEntityContext):
    ENTITY = _("container distribution")
    ENTITIES = _("container distributions")
    HREF = "container_container_distribution_href"
    LIST_ID = "distributions_container_container_list"
    READ_ID = "distributions_container_container_read"
    CREATE_ID = "distributions_container_container_create"
    UPDATE_ID = "distributions_container_container_partial_update"
    DELETE_ID = "distributions_container_container_delete"

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        body = super().preprocess_body(body)
        version = body.pop("version", None)
        if version is not None:
            repository_href = body.pop("repository")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        return body


class PulpContainerRemoteContext(PulpRemoteContext):
    ENTITY = _("container remote")
    ENTITIES = _("container remotes")
    HREF = "container_container_remote_href"
    LIST_ID = "remotes_container_container_list"
    CREATE_ID = "remotes_container_container_create"
    UPDATE_ID = "remotes_container_container_partial_update"
    DELETE_ID = "remotes_container_container_delete"
    NULLABLES = PulpRemoteContext.NULLABLES | {"include_tags", "exclude_tags"}


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
    CAPABILITIES = {
        "sync": [PluginRequirement("container")],
        "pulpexport": [PluginRequirement("container", "2.8.0.dev")],
    }


class PulpContainerPushRepositoryContext(PulpRepositoryContext):
    HREF = "container_container_push_repository_href"
    LIST_ID = "repositories_container_container_push_list"
    READ_ID = "repositories_container_container_push_read"
    # CREATE_ID = "repositories_container_container_push_create"
    # UPDATE_ID = "repositories_container_container_push_update"
    # DELETE_ID = "repositories_container_container_push_delete"
    VERSION_CONTEXT = PulpContainerPushRepositoryVersionContext


registered_repository_contexts["container:container"] = PulpContainerRepositoryContext
registered_repository_contexts["container:push"] = PulpContainerPushRepositoryContext
