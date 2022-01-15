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
    ID_PREFIX = "content_python_packages"


class PulpPythonDistributionContext(PulpEntityContext):
    ENTITY = _("python distribution")
    ENTITIES = _("python distributions")
    HREF = "python_python_distribution_href"
    ID_PREFIX = "distributions_python_pypi"
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
    ID_PREFIX = "publications_python_pypi"

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
    ID_PREFIX = "remotes_python_python"


class PulpPythonRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "python_python_repository_version_href"
    ID_PREFIX = "repositories_python_python_versions"


class PulpPythonRepositoryContext(PulpRepositoryContext):
    HREF = "python_python_repository_href"
    ID_PREFIX = "repositories_python_python"
    VERSION_CONTEXT = PulpPythonRepositoryVersionContext


registered_repository_contexts["python:python"] = PulpPythonRepositoryContext
