import gettext
from pulpcore.cli.common.context import (
    PulpEntityContext,
    PulpRepositoryContext,
    PulpContentGuardContext,
    registered_repository_contexts,
)
from pulpcore.cli.common.i18n import _

_ = gettext.gettext


class PulpContainerRepositoryContext(PulpRepositoryContext):
    ENTITY = _("container repository")
    ENTITIES = _("container repositories")
    HREF = "container_container_repo_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]
    CAPABILITIES = {"sync": ["remote"]}

    def sync(self, href: str, body: dict) -> dict:
        body = body.copy()
        body["repository"] = href
        return self.call("sync", body)


class PulpContainerPushRepositoryContext(PulpRepositoryContext):
    ENTITY = _("container push repository")
    ENTITIES = _("container push repositories")
    HREF = "container_container_push_repo_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]
    CAPABILITIES = {"sync": ["remote"]}

    def sync(self, href: str, body: dict) -> dict:
        body = body.copy()
        body["repository"] = href
        return self.call("sync", body)


class PulpContainerDistributionContext(PulpEntityContext):
    ENTITY = _("container distribution")
    ENTITIES = _("container distributions")
    HREF = "container_distribution_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]


class PulpContainerContentGuardContext(PulpContentGuardContext):
    ENTITY = _("container content guard")
    ENTITIES = _("container content guards")
    HREF = "container_content_guard_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]


class PulpContainerNamespaceContext(PulpEntityContext):
    ENTITY = _("container namespace")
    ENTITIES = _("container namespaces")
    HREF = "container_container_namespace_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]


class PulpContainerRecursiveAddContext(PulpEntityContext):
    ENTITY = _("container recursive add")
    ENTITIES = _("container recursive adds")
    HREF = "container_container_recursive_add_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]


class PulpContainerRecursiveRemoveContext(PulpEntityContext):
    ENTITY = _("container recursive remove")
    ENTITIES = _("container recursive removes")
    HREF = "container_container_recursive_remove_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]


class PulpContainerTagContext(PulpEntityContext):
    ENTITY = _("container tag")
    ENTITIES = _("container tags")
    HREF = "container_container_tag_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]


class PulpContainerManifestContext(PulpEntityContext):
    ENTITY = _("container manifest")
    ENTITIES = _("container manifests")
    HREF = "container_container_manifest_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]


class PulpContainerBlobContext(PulpEntityContext):
    ENTITY = _("container blob")
    ENTITIES = _("container blobs")
    HREF = "container_container_blob_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]


class PulpContainerImageContext(PulpEntityContext):
    ENTITY = _("container image")
    ENTITIES = _("container images")
    HREF = "container_container_image_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]


class PulpContainerSignatureContext(PulpEntityContext):
    ENTITY = _("container signature")
    ENTITIES = _("container signatures")
    HREF = "container_container_signature_href"
    ID_PREFIX = "container"
    NEEDS_PLUGINS = ["container"]


registered_repository_contexts["container:container"] = PulpContainerRepositoryContext
registered_repository_contexts["container:push"] = PulpContainerPushRepositoryContext