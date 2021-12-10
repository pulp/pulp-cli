from typing import ClassVar

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


class PulpPythonContentContext(PulpContentContext):
    ENTITY = _("python package")
    ENTITIES = _("python packages")
    HREF = "python_python_package_content_href"
    LIST_ID = "content_python_packages_list"
    READ_ID = "content_python_packages_read"
    CREATE_ID = "content_python_packages_create"


class PulpPythonDistributionContext(PulpEntityContext):
    ENTITY = _("python distribution")
    ENTITIES = _("python distributions")
    HREF = "python_python_distribution_href"
    LIST_ID = "distributions_python_pypi_list"
    READ_ID = "distributions_python_pypi_read"
    CREATE_ID = "distributions_python_pypi_create"
    UPDATE_ID = "distributions_python_pypi_partial_update"
    DELETE_ID = "distributions_python_pypi_delete"
    NULLABLES = {"publication", "repository"}

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        body = super().preprocess_body(body)
        if self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.16.0.dev")):
            if "repository" in body and "publication" not in body:
                body["publication"] = None
            if "repository" not in body and "publication" in body:
                body["repository"] = None
        return body


class PulpPythonPublicationContext(PulpEntityContext):
    ENTITY = _("python publication")
    ENTITIES = _("python publications")
    HREF = "python_python_publication_href"
    LIST_ID = "publications_python_pypi_list"
    READ_ID = "publications_python_pypi_read"
    CREATE_ID = "publications_python_pypi_create"
    DELETE_ID = "publications_python_pypi_delete"

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        body = super().preprocess_body(body)
        version = body.pop("version", None)
        if version is not None:
            repository_href = body.pop("repository")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        return body


class PulpPythonRemoteContext(PulpRemoteContext):
    ENTITY = _("python remote")
    ENTITIES = _("python remotes")
    HREF = "python_python_remote_href"
    LIST_ID = "remotes_python_python_list"
    CREATE_ID = "remotes_python_python_create"
    BANDERSNATCH_ID: ClassVar[str] = "remotes_python_python_from_bandersnatch"
    UPDATE_ID = "remotes_python_python_partial_update"
    DELETE_ID = "remotes_python_python_delete"


class PulpPythonRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "python_python_repository_version_href"
    LIST_ID = "repositories_python_python_versions_list"
    READ_ID = "repositories_python_python_versions_read"
    DELETE_ID = "repositories_python_python_versions_delete"
    REPAIR_ID = "repositories_python_python_versions_repair"


class PulpPythonRepositoryContext(PulpRepositoryContext):
    HREF = "python_python_repository_href"
    LIST_ID = "repositories_python_python_list"
    READ_ID = "repositories_python_python_read"
    CREATE_ID = "repositories_python_python_create"
    UPDATE_ID = "repositories_python_python_partial_update"
    DELETE_ID = "repositories_python_python_delete"
    SYNC_ID = "repositories_python_python_sync"
    MODIFY_ID = "repositories_python_python_modify"
    VERSION_CONTEXT = PulpPythonRepositoryVersionContext


registered_repository_contexts["python:python"] = PulpPythonRepositoryContext
