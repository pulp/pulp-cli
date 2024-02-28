import typing as t

from pulp_glue.common.context import (
    EntityDefinition,
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


class PulpAnsibleCollectionVersionContext(PulpContentContext):
    PLUGIN = "ansible"
    RESOURCE_TYPE = "collection_version"
    ENTITY = _("ansible collection version")
    ENTITIES = _("ansible collection versions")
    HREF = "ansible_collection_version_href"
    ID_PREFIX = "content_ansible_collection_versions"
    UPLOAD_ID: t.ClassVar[str] = "upload_collection"
    NEEDS_PLUGINS = [PluginRequirement("ansible", specifier=">=0.7.0")]
    CAPABILITIES = {"upload": [PluginRequirement("ansible", specifier=">=0.16.0")]}

    def upload(self, file: t.IO[bytes], **kwargs: t.Any) -> t.Any:  # type:ignore
        repository: t.Optional[PulpRepositoryContext] = kwargs.pop("repository", None)
        if self.capable("upload"):
            chunk_size: int = kwargs.pop("chunk_size", 1000000)
            return super().upload(file, chunk_size, repository, **kwargs)
        else:
            result = self.call("upload", body={"file": file})
            self.pulp_href = result["created_resources"][0]
            if repository:
                repository.modify(add_content=[self.pulp_href])
            return self.entity


class PulpAnsibleRoleContext(PulpContentContext):
    PLUGIN = "ansible"
    RESOURCE_TYPE = "role"
    ENTITY = _("ansible role")
    ENTITIES = _("ansible roles")
    HREF = "ansible_role_href"
    ID_PREFIX = "content_ansible_roles"
    NEEDS_PLUGINS = [PluginRequirement("ansible", specifier=">=0.7.0")]


class PulpAnsibleCollectionVersionSignatureContext(PulpContentContext):
    PLUGIN = "ansible"
    RESOURCE_TYPE = "collection_version_signature"
    ENTITY = _("ansible collection version signature")
    ENTITIES = _("ansible collection version signatures")
    HREF = _("ansible_collection_version_signature_href")
    ID_PREFIX = "content_ansible_collection_signatures"
    NEEDS_PLUGINS = [PluginRequirement("ansible", specifier=">=0.12.0")]

    def create(
        self,
        body: EntityDefinition,
        parameters: t.Optional[t.Mapping[str, t.Any]] = None,
        non_blocking: bool = False,
    ) -> t.Any:
        self.pulp_ctx.needs_plugin(
            PluginRequirement(
                "ansible", specifier=">=0.13.0", feature=_("collection version creation")
            )
        )
        return super().create(body=body, parameters=parameters, non_blocking=non_blocking)


class PulpAnsibleDistributionContext(PulpDistributionContext):
    PLUGIN = "ansible"
    RESOURCE_TYPE = "ansible"
    ENTITY = _("ansible distribution")
    ENTITIES = _("ansible distributions")
    HREF = "ansible_ansible_distribution_href"
    ID_PREFIX = "distributions_ansible_ansible"
    NEEDS_PLUGINS = [PluginRequirement("ansible", specifier=">=0.7.0")]

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        version = body.pop("version", None)
        if version is not None:
            repository_href = body.pop("repository")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        return body


class PulpAnsibleRoleRemoteContext(PulpRemoteContext):
    PLUGIN = "ansible"
    RESOURCE_TYPE = "role"
    ENTITY = _("role remote")
    ENTITIES = _("role remotes")
    HREF = "ansible_role_remote_href"
    ID_PREFIX = "remotes_ansible_role"
    HREF_PATTERN = r"remotes/(?P<plugin>ansible)/(?P<resource_type>role)/"
    NEEDS_PLUGINS = [PluginRequirement("ansible", specifier=">=0.7.0")]


class PulpAnsibleCollectionRemoteContext(PulpRemoteContext):
    PLUGIN = "ansible"
    RESOURCE_TYPE = "collection"
    ENTITY = _("collection remote")
    ENTITIES = _("collection remotes")
    HREF = "ansible_collection_remote_href"
    ID_PREFIX = "remotes_ansible_collection"
    HREF_PATTERN = r"remotes/(?P<plugin>ansible)/(?P<resource_type>collection)/"
    NEEDS_PLUGINS = [PluginRequirement("ansible", specifier=">=0.7.0")]

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if "requirements" in body.keys():
            body["requirements_file"] = body.pop("requirements")
        return body


class PulpAnsibleRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "ansible_ansible_repository_version_href"
    ID_PREFIX = "repositories_ansible_ansible_versions"
    NEEDS_PLUGINS = [PluginRequirement("ansible", specifier=">=0.7.0")]


class PulpAnsibleRepositoryContext(PulpRepositoryContext):
    PLUGIN = "ansible"
    RESOURCE_TYPE = "ansible"
    HREF = "ansible_ansible_repository_href"
    ID_PREFIX = "repositories_ansible_ansible"
    ENTITY = _("ansible repository")
    ENTITIES = _("ansible repositories")
    VERSION_CONTEXT = PulpAnsibleRepositoryVersionContext
    CAPABILITIES = {
        "sync": [PluginRequirement("ansible")],
        "pulpexport": [PluginRequirement("ansible")],
    }
    NULLABLES = PulpRepositoryContext.NULLABLES | {"gpgkey"}
    NEEDS_PLUGINS = [PluginRequirement("ansible", specifier=">=0.7.0")]
