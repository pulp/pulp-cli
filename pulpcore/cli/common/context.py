import warnings

from pulp_glue.common.context import EntityDefinition  # noqa: F401
from pulp_glue.common.context import (
    EntityFieldDefinition,
    PluginRequirement,
    PreprocessedEntityDefinition,
    PulpACSContext,
    PulpContentContext,
    PulpContext,
    PulpDistributionContext,
    PulpEntityContext,
    PulpException,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    registered_repository_contexts,
)

warnings.warn(
    DeprecationWarning("This module is deprecated. Import from pulp_glue.common.context instead.")
)

__all__ = [
    "EntityDefinition",
    "EntityFieldDefinition",
    "PluginRequirement",
    "PreprocessedEntityDefinition",
    "PulpACSContext",
    "PulpContentContext",
    "PulpContext",
    "PulpDistributionContext",
    "PulpEntityContext",
    "PulpException",
    "PulpRemoteContext",
    "PulpRepositoryContext",
    "PulpRepositoryVersionContext",
    "registered_repository_contexts",
]
