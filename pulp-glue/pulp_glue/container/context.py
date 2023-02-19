from typing import Any, List, Optional

from pulp_glue.common.context import (
    EntityDefinition,
    PluginRequirement,
    PulpContentContext,
    PulpDistributionContext,
    PulpEntityContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    registered_repository_contexts,
)
from pulp_glue.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


class PulpContainerBlobContext(PulpContentContext):
    ENTITY = _("container blob")
    ENTITIES = _("container blobs")
    HREF = "container_blob_href"
    ID_PREFIX = "content_container_blobs"
    NEEDS_PLUGINS = [PluginRequirement("container", min="2.3.0")]


class PulpContainerManifestContext(PulpContentContext):
    ENTITY = _("container manifest")
    ENTITIES = _("container manifests")
    HREF = "container_manifest_href"
    ID_PREFIX = "content_container_manifests"
    NEEDS_PLUGINS = [PluginRequirement("container", min="2.3.0")]


class PulpContainerTagContext(PulpContentContext):
    ENTITY = _("container tag")
    ENTITIES = _("container tags")
    HREF = "container_tag_href"
    ID_PREFIX = "content_container_tags"
    NEEDS_PLUGINS = [PluginRequirement("container", min="2.3.0")]

    def find(self, **kwargs: Any) -> Any:
        if "digest" in kwargs and isinstance(kwargs["digest"], str):
            kwargs["digest"] = [kwargs["digest"]]
        return super().find(**kwargs)


class PulpContainerNamespaceContext(PulpEntityContext):
    ENTITY = _("container namespace")
    ENTITIES = _("container namespaces")
    HREF = "container_container_namespace_href"
    ID_PREFIX = "pulp_container_namespaces"
    HREF_PATTERN = r"(?P<plugin>pulp_container)/(?P<resource_type>namespaces)/"
    NEEDS_PLUGINS = [PluginRequirement("container", min="2.3.0")]
    CAPABILITIES = {"roles": [PluginRequirement("container", min="2.11.0")]}


class PulpContainerDistributionContext(PulpDistributionContext):
    ENTITY = _("container distribution")
    ENTITIES = _("container distributions")
    HREF = "container_container_distribution_href"
    ID_PREFIX = "distributions_container_container"
    NULLABLES = {"repository_version", "repository"}
    NEEDS_PLUGINS = [PluginRequirement("container", min="2.3.0")]
    CAPABILITIES = {"roles": [PluginRequirement("container", min="2.11.0")]}

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        version = body.pop("version", None)
        if version is not None:
            repository_href = body.pop("repository")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        return body


class PulpContainerRemoteContext(PulpRemoteContext):
    ENTITY = _("container remote")
    ENTITIES = _("container remotes")
    HREF = "container_container_remote_href"
    ID_PREFIX = "remotes_container_container"
    NULLABLES = PulpRemoteContext.NULLABLES | {"include_tags", "exclude_tags"}
    NEEDS_PLUGINS = [PluginRequirement("container", min="2.3.0")]
    CAPABILITIES = {"roles": [PluginRequirement("container", min="2.11.0")]}


class PulpContainerRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "container_container_repository_version_href"
    ID_PREFIX = "repositories_container_container_versions"
    NEEDS_PLUGINS = [PluginRequirement("container", min="2.3.0")]


class PulpContainerPushRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "container_container_push_repository_version_href"
    ID_PREFIX = "repositories_container_container_push_versions"
    NEEDS_PLUGINS = [PluginRequirement("container", min="2.3.0")]


class PulpContainerBaseRepositoryContext(PulpRepositoryContext):
    NEEDS_PLUGINS = [PluginRequirement("container", min="2.3.0")]

    def tag(self, tag: str, digest: str) -> Any:
        self.needs_capability("tag")
        return self.call(
            "tag",
            parameters={self.HREF: self.pulp_href},
            body={"tag": tag, "digest": digest},
        )

    def untag(self, tag: str) -> Any:
        self.needs_capability("tag")
        return self.call(
            "untag",
            parameters={self.HREF: self.pulp_href},
            body={"tag": tag},
        )


class PulpContainerRepositoryContext(PulpContainerBaseRepositoryContext):
    HREF = "container_container_repository_href"
    ID_PREFIX = "repositories_container_container"
    ENTITY = _("container repository")
    ENTITIES = _("container repositories")
    VERSION_CONTEXT = PulpContainerRepositoryVersionContext
    HREF_PATTERN = r"repositories/(?P<plugin>container)/(?P<resource_type>container)/"
    CAPABILITIES = {
        "sync": [PluginRequirement("container")],
        "pulpexport": [PluginRequirement("container", min="2.8.0")],
        "tag": [PluginRequirement("container", min="2.3.0")],
        "roles": [PluginRequirement("container", min="2.11.0")],
    }

    def modify(
        self,
        href: Optional[str] = None,
        add_content: Optional[List[str]] = None,
        remove_content: Optional[List[str]] = None,
        base_version: Optional[str] = None,
    ) -> Any:
        if remove_content:
            self.call(
                "remove",
                parameters={self.HREF: href or self.pulp_href},
                body={"content_units": remove_content},
            )
        if add_content:
            self.call(
                "add",
                parameters={self.HREF: href or self.pulp_href},
                body={"content_units": add_content},
            )

    def copy_tag(self, source_href: str, tags: Optional[List[str]]) -> Any:
        body = {"source_repository_version": source_href, "names": tags}
        return self.call("copy_tags", parameters={self.HREF: self.pulp_href}, body=body)

    def copy_manifest(
        self,
        source_href: str,
        digests: Optional[List[str]],
        media_types: Optional[List[str]],
    ) -> Any:
        body = {
            "source_repository_version": source_href,
            "digests": digests,
            "media_types": media_types,
        }
        return self.call("copy_manifests", parameters={self.HREF: self.pulp_href}, body=body)


class PulpContainerPushRepositoryContext(PulpContainerBaseRepositoryContext):
    HREF = "container_container_push_repository_href"
    ID_PREFIX = "repositories_container_container_push"
    ENTITY = _("push container repository")
    ENTITIES = _("push container repositories")
    VERSION_CONTEXT = PulpContainerPushRepositoryVersionContext
    HREF_PATTERN = r"repositories/(?P<plugin>container)/(?P<resource_type>container-push)/"
    CAPABILITIES = {
        "tag": [PluginRequirement("container", min="2.3.0")],
        "roles": [PluginRequirement("container", min="2.11.0")],
        "remove": [PluginRequirement("container", min="2.4.0")],
    }

    def remove_image(self, digest: str) -> Any:
        self.needs_capability("remove")
        body = {"digest": digest}
        return self.call("remove_image", parameters={self.HREF: self.pulp_href}, body=body)


registered_repository_contexts["container:container"] = PulpContainerRepositoryContext
registered_repository_contexts["container:push"] = PulpContainerPushRepositoryContext
