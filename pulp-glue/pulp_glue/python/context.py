from pulp_glue.common.context import (
    EntityDefinition,
    PluginRequirement,
    PulpContentContext,
    PulpDistributionContext,
    PulpPublicationContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    registered_repository_contexts,
)
from pulp_glue.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


class PulpPythonContentContext(PulpContentContext):
    ENTITY = _("python package")
    ENTITIES = _("python packages")
    HREF = "python_python_package_content_href"
    ID_PREFIX = "content_python_packages"
    NEEDS_PLUGINS = [PluginRequirement("python", min="3.1.0")]
    CAPABILITIES = {"upload": []}


class PulpPythonDistributionContext(PulpDistributionContext):
    ENTITY = _("python distribution")
    ENTITIES = _("python distributions")
    HREF = "python_python_distribution_href"
    ID_PREFIX = "distributions_python_pypi"
    NULLABLES = {"publication", "repository"}
    NEEDS_PLUGINS = [PluginRequirement("python", min="3.1.0")]

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if "allow_uploads" in body:
            self.pulp_ctx.needs_plugin(PluginRequirement("python", min="3.4.0"))
        if "remote" in body:
            self.pulp_ctx.needs_plugin(PluginRequirement("python", min="3.6.0"))
        if self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.16.0")):
            if "repository" in body and "publication" not in body:
                body["publication"] = None
            if "repository" not in body and "publication" in body:
                body["repository"] = None
        return body


class PulpPythonPublicationContext(PulpPublicationContext):
    ENTITY = _("python publication")
    ENTITIES = _("python publications")
    HREF = "python_python_publication_href"
    ID_PREFIX = "publications_python_pypi"
    NEEDS_PLUGINS = [PluginRequirement("python", min="3.1.0")]

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
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
    NEEDS_PLUGINS = [PluginRequirement("python", min="3.1.0")]

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if "keep_latest_packages" in body or "package_types" in body or "exclude_platforms" in body:
            self.pulp_ctx.needs_plugin(PluginRequirement("python", min="3.2.0"))
        return body


class PulpPythonRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "python_python_repository_version_href"
    ID_PREFIX = "repositories_python_python_versions"
    NEEDS_PLUGINS = [PluginRequirement("python", min="3.1.0")]


class PulpPythonRepositoryContext(PulpRepositoryContext):
    HREF = "python_python_repository_href"
    ENTITY = _("python repository")
    ENTITIES = _("python repositories")
    ID_PREFIX = "repositories_python_python"
    VERSION_CONTEXT = PulpPythonRepositoryVersionContext
    CAPABILITIES = {"sync": [PluginRequirement("python")]}
    NEEDS_PLUGINS = [PluginRequirement("python", min="3.1.0")]

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if "autopublish" in body:
            self.pulp_ctx.needs_plugin(PluginRequirement("python", min="3.3.0"))
        return body


registered_repository_contexts["python:python"] = PulpPythonRepositoryContext
