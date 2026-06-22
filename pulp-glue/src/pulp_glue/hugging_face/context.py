from pulp_glue.common.context import (
    EntityDefinition,
    PluginRequirement,
    PulpDistributionContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)
from pulp_glue.common.i18n import get_translation

translation = get_translation(__package__)
_ = translation.gettext


class PulpHuggingFaceRemoteContext(PulpRemoteContext):
    PLUGIN = "hugging_face"
    RESOURCE_TYPE = "hugging-face"
    ENTITY = _("hugging face remote")
    ENTITIES = _("hugging face remotes")
    HREF = "hugging_face_hugging_face_remote_href"
    ID_PREFIX = "remotes_hugging_face_hugging_face"
    NEEDS_PLUGINS = [PluginRequirement("hugging_face", specifier=">=0.1.0")]


class PulpHuggingFaceDistributionContext(PulpDistributionContext):
    PLUGIN = "hugging_face"
    RESOURCE_TYPE = "hugging-face"
    ENTITY = _("hugging face distribution")
    ENTITIES = _("hugging face distributions")
    HREF = "hugging_face_hugging_face_distribution_href"
    ID_PREFIX = "distributions_hugging_face_hugging_face"
    NEEDS_PLUGINS = [PluginRequirement("hugging_face", specifier=">=0.1.0")]

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if not partial and self.pulp_ctx.has_plugin(
            PluginRequirement("core", specifier=">=3.16.0")
        ):
            body.setdefault("repository", None)
            body.setdefault("remote", None)
        return body


class PulpHuggingFaceRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "hugging_face_hugging_face_repository_version_href"
    ID_PREFIX = "repositories_hugging_face_hugging_face_versions"
    NEEDS_PLUGINS = [PluginRequirement("hugging_face", specifier=">=0.1.0")]


class PulpHuggingFaceRepositoryContext(PulpRepositoryContext):
    PLUGIN = "hugging_face"
    RESOURCE_TYPE = "hugging-face"
    ENTITY = _("hugging face repository")
    ENTITIES = _("hugging face repositories")
    HREF = "hugging_face_hugging_face_repository_href"
    ID_PREFIX = "repositories_hugging_face_hugging_face"
    VERSION_CONTEXT = PulpHuggingFaceRepositoryVersionContext
    NEEDS_PLUGINS = [PluginRequirement("hugging_face", specifier=">=0.1.0")]
