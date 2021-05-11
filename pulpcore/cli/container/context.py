import gettext
import sys
from typing import Any

import click

from pulpcore.cli.common.context import (
    EntityDefinition,
    PulpEntityContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)

_ = gettext.gettext


class PulpContainerNamespaceContext(PulpEntityContext):
    ENTITY = "container namespace"
    ENTITIES = "container namespaces"
    HREF = "container_container_namespace_href"
    LIST_ID = "pulp_container_namespaces_list"
    READ_ID = "pulp_container_namespaces_read"
    CREATE_ID = "pulp_container_namespaces_create"
    DELETE_ID = "pulp_container_namespaces_delete"

    def find(self, **kwargs: Any) -> Any:
        """Workaroud for the missing ability to filter"""
        if self.pulp_ctx.has_plugin("container", min_version="2.3"):
            # Workaround not needed anymore
            return super().find(**kwargs)
        search_result = self.list(limit=sys.maxsize, offset=0, parameters={})
        for key, value in kwargs.items():
            search_result = [res for res in search_result if res[key] == value]
        if len(search_result) != 1:
            raise click.ClickException(f"Could not find {self.ENTITY} with {kwargs}.")
        return search_result[0]


class PulpContainerDistributionContext(PulpEntityContext):
    ENTITY = "container distribution"
    ENTITIES = "container distributions"
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
    ENTITY = "container remote"
    ENTITIES = "container remotes"
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
