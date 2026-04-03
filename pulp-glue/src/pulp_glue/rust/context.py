from pulp_glue.common.context import (
    PluginRequirement,
    PulpContentContext,
    PulpDistributionContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)
from pulp_glue.common.i18n import get_translation

translation = get_translation(__package__)
_ = translation.gettext


class PulpRustContentContext(PulpContentContext):
    PLUGIN = "rust"
    RESOURCE_TYPE = "packages"
    ENTITY = _("rust package")
    ENTITIES = _("rust packages")
    HREF = "rust_rust_package_content_href"
    ID_PREFIX = "content_rust_packages"
    NEEDS_PLUGINS = [PluginRequirement("rust")]


class PulpRustDistributionContext(PulpDistributionContext):
    PLUGIN = "rust"
    RESOURCE_TYPE = "rust"
    ENTITY = _("rust distribution")
    ENTITIES = _("rust distributions")
    HREF = "rust_rust_distribution_href"
    ID_PREFIX = "distributions_rust_rust"
    NEEDS_PLUGINS = [PluginRequirement("rust")]


class PulpRustRemoteContext(PulpRemoteContext):
    PLUGIN = "rust"
    RESOURCE_TYPE = "rust"
    ENTITY = _("rust remote")
    ENTITIES = _("rust remotes")
    HREF = "rust_rust_remote_href"
    ID_PREFIX = "remotes_rust_rust"
    NEEDS_PLUGINS = [PluginRequirement("rust")]


class PulpRustRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "rust_rust_repository_version_href"
    ID_PREFIX = "repositories_rust_rust_versions"
    NEEDS_PLUGINS = [PluginRequirement("rust")]


class PulpRustRepositoryContext(PulpRepositoryContext):
    PLUGIN = "rust"
    RESOURCE_TYPE = "rust"
    HREF = "rust_rust_repository_href"
    ENTITY = _("rust repository")
    ENTITIES = _("rust repositories")
    ID_PREFIX = "repositories_rust_rust"
    VERSION_CONTEXT = PulpRustRepositoryVersionContext
    CAPABILITIES = {}
    NULLABLES = PulpRepositoryContext.NULLABLES | {"remote"}
    NEEDS_PLUGINS = [PluginRequirement("rust")]
