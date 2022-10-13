import datetime
import hashlib
import os
import sys
from typing import IO, Any, ClassVar, Dict, List, Optional

from pulpcore.cli.common.context import (
    EntityDefinition,
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
    PulpException,
)
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


class PulpAccessPolicyContext(PulpEntityContext):
    ENTITY = _("access policy")
    ENTITIES = _("access policies")
    HREF = "access_policy_href"
    ID_PREFIX = "access_policies"

    def reset(self) -> Any:
        self.pulp_ctx.needs_plugin(PluginRequirement("core", min="3.17.0"))
        return self.call("reset", parameters={self.HREF: self.pulp_href})

    def preprocess_entity(self, body: EntityDefinition, partial: bool = False) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if not self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.17.0")):
            if "creation_hooks" in body:
                body["permissions_assignment"] = body.pop("creation_hooks")
        return body


class PulpArtifactContext(PulpEntityContext):
    ENTITY = _("artifact")
    ENTITIES = _("artifacts")
    HREF = "artifact_href"
    ID_PREFIX = "artifacts"

    def upload(self, file: IO[bytes], chunk_size: int = 1000000) -> Any:
        upload_ctx = PulpUploadContext(self.pulp_ctx)
        size = os.path.getsize(file.name)

        sha256 = hashlib.sha256()
        for chunk in iter(lambda: file.read(chunk_size), b""):
            sha256.update(chunk)
        sha256_digest = sha256.hexdigest()
        file.seek(0)

        # check whether the file exists before uploading
        result = self.list(limit=1, offset=0, parameters={"sha256": sha256_digest})
        if len(result) > 0:
            self.pulp_ctx.echo(_("Artifact already exists."), err=True)
            return result[0]["pulp_href"]

        self.pulp_ctx.echo(_("Uploading file {filename}").format(filename=file.name), err=True)

        if chunk_size > size:
            # if chunk_size is bigger than the file size, just upload it directly
            artifact: Dict[str, Any] = self.create(
                {"sha256": sha256_digest}, uploads={"file": file.read()}
            )
            return artifact["pulp_href"]

        upload_href = upload_ctx.upload_file(file, chunk_size)

        self.pulp_ctx.echo(_("Creating artifact."), err=True)
        try:
            task = upload_ctx.commit(
                upload_href,
                sha256_digest,
            )
            result = task["created_resources"][0]
        except Exception as e:
            upload_ctx.delete(upload_href)
            raise e
        return result


class PulpExporterContext(PulpEntityContext):
    ENTITY = _("Pulp exporter")
    ENTITIES = _("Pulp exporters")
    HREF = "pulp_exporter_href"
    ID_PREFIX = "exporters_core_pulp"


class PulpExportContext(PulpEntityContext):
    ENTITY = _("Pulp export")
    ENTITIES = _("Pulp exports")
    HREF = "pulp_pulp_export_href"
    ID_PREFIX = "exporters_core_pulp_exports"
    exporter: EntityDefinition

    @property
    def scope(self) -> Dict[str, Any]:
        return {PulpExporterContext.HREF: self.exporter["pulp_href"]}


class PulpGroupContext(PulpEntityContext):
    ENTITY = _("user group")
    ENTITIES = _("user groups")
    # Handled by a workaround
    # HREF = "group_href"
    ID_PREFIX = "groups"
    CAPABILITIES = {"roles": [PluginRequirement("core", "3.17.0")]}

    @property
    def HREF(self) -> str:  # type:ignore
        if not self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.17.0")):
            return "auth_group_href"
        return "group_href"


class PulpGroupPermissionContext(PulpEntityContext):
    ENTITY = _("group permission")
    ENTITIES = _("group permissions")
    NEEDS_PLUGINS = [PluginRequirement("core", max="3.20.0", feature=_("group permissions"))]
    group_ctx: PulpGroupContext

    def __init__(self, pulp_ctx: PulpContext, group_ctx: PulpGroupContext) -> None:
        super().__init__(pulp_ctx)
        self.group_ctx = group_ctx

    def call(
        self,
        operation: str,
        non_blocking: bool = False,
        parameters: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        uploads: Optional[Dict[str, bytes]] = None,
        validate_body: bool = False,
    ) -> Any:
        """Workaroud because the openapi spec for GroupPermissions has always been broken.

        This will probably not be fixed upstream, and GroupPermissions are removed from pulpcore.
        So we just skip linting here.
        """
        return super().call(
            operation,
            non_blocking=non_blocking,
            parameters=parameters,
            body=body,
            uploads=uploads,
            validate_body=validate_body,
        )

    def find(self, **kwargs: Any) -> Any:
        """Workaroud for the missing ability to filter"""
        # # TODO fix upstream and adjust to guard for the proper version
        # # https://pulp.plan.io/issues/8241
        # if self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.99.dev")):
        #     # Workaround not needed anymore
        #     return super().find(**kwargs)
        search_result = self.list(limit=sys.maxsize, offset=0, parameters={})
        for key, value in kwargs.items():
            search_result = [res for res in search_result if res[key] == value]
        if len(search_result) != 1:
            raise PulpException(
                _("Could not find {entity} with {kwargs}.").format(
                    entity=self.ENTITY, kwargs=kwargs
                )
            )
        return search_result[0]

    @property
    def scope(self) -> Dict[str, Any]:
        return {self.group_ctx.HREF: self.group_ctx.pulp_href}


class PulpGroupModelPermissionContext(PulpGroupPermissionContext):
    ENTITY = _("group model permission")
    ENTITIES = _("group model permissions")
    # Handled by a workaround
    # HREF = "groups_model_permission_href"
    ID_PREFIX = "groups_model_permissions"

    @property
    def HREF(self) -> str:  # type:ignore
        if not self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.17.0")):
            return "auth_groups_model_permission_href"
        return "groups_model_permission_href"


class PulpGroupObjectPermissionContext(PulpGroupPermissionContext):
    ENTITY = _("group object permission")
    ENTITIES = _("group object permissions")
    # Handled by a workaround
    # HREF = "groups_object_permission_href"
    ID_PREFIX = "groups_object_permissions"

    @property
    def HREF(self) -> str:  # type:ignore
        if not self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.17.0")):
            return "auth_groups_object_permission_href"
        return "groups_object_permission_href"


class PulpGroupRoleContext(PulpEntityContext):
    ENTITY = _("group role")
    ENTITIES = _("group roles")
    HREF = "groups_group_role_href"
    ID_PREFIX = "groups_roles"
    NULLABLES = {"content_object"}
    group_ctx: PulpGroupContext

    def __init__(self, pulp_ctx: PulpContext, group_ctx: PulpGroupContext) -> None:
        super().__init__(pulp_ctx)
        self.group_ctx = group_ctx

    @property
    def scope(self) -> Dict[str, Any]:
        return {self.group_ctx.HREF: self.group_ctx.pulp_href}


class PulpGroupUserContext(PulpEntityContext):
    ENTITY = _("group user")
    ENTITIES = _("group users")
    # Handled by a workaround
    # HREF = "groups_user_href"
    ID_PREFIX = "groups_users"
    group_ctx: PulpGroupContext

    @property
    def HREF(self) -> str:  # type:ignore
        if not self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.17.0")):
            return "auth_groups_user_href"
        return "groups_user_href"

    def __init__(self, pulp_ctx: PulpContext, group_ctx: PulpGroupContext) -> None:
        super().__init__(pulp_ctx)
        self.group_ctx = group_ctx

    @property
    def scope(self) -> Dict[str, Any]:
        return {self.group_ctx.HREF: self.group_ctx.pulp_href}


class PulpContentGuardContext(PulpEntityContext):
    ENTITY = "content guard"
    ENTITIES = "content guards"
    ID_PREFIX = "contentguards"
    HREF_PATTERN = r"contentguards/(?P<plugin>\w+)/(?P<resource_type>\w+)/"


class PulpContentRedirectContentGuardContext(PulpEntityContext):
    ENTITY = "content redirect content guard"
    ENTITIES = "content redirect content guards"
    HREF = "content_redirect_content_guard_href"
    ID_PREFIX = "contentguards_core_content_redirect"
    NEEDS_PLUGINS = [PluginRequirement("core", "3.18.0")]


class PulpDistributionContext(PulpEntityContext):
    ENTITY = _("distribution")
    ENTITIES = _("distributions")
    ID_PREFIX = "distributions"
    HREF_PATTERN = r"distributions/(?P<plugin>\w+)/(?P<resource_type>\w+)/"


class PulpImporterContext(PulpEntityContext):
    ENTITY = _("Pulp importer")
    ENTITIES = _("Pulp importers")
    HREF = "pulp_importer_href"
    ID_PREFIX = "importers_core_pulp"


class PulpPublicationContext(PulpEntityContext):
    ENTITY = _("Pulp publication")
    ENTITIES = _("Pulp publications")
    ID_PREFIX = "publications"
    HREF_PATTERN = r"publications/(?P<plugin>\w+)/(?P<resource_type>\w+)/"


class PulpRbacContentGuardContext(PulpContentGuardContext):
    ENTITY = "RBAC content guard"
    ENTITIES = "RBAC content guards"
    HREF = "r_b_a_c_content_guard_href"
    ID_PREFIX = "contentguards_core_rbac"
    DOWNLOAD_ROLE: ClassVar[str] = "core.rbaccontentguard_downloader"
    CAPABILITIES = {"roles": [PluginRequirement("core", "3.17.0")]}
    NEEDS_PLUGINS = [PluginRequirement("core", "3.15.0")]

    def assign(self, href: str, users: Optional[List[str]], groups: Optional[List[str]]) -> Any:
        if self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.17.0")):
            body: EntityDefinition = {"users": users, "groups": groups}
            body["role"] = self.DOWNLOAD_ROLE
            return self.call("add_role", parameters={self.HREF: href}, body=body)
        else:
            body = {"usernames": users, "groupnames": groups}
            return self.call("assign_permission", parameters={self.HREF: href}, body=body)

    def remove(self, href: str, users: Optional[List[str]], groups: Optional[List[str]]) -> Any:
        if self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.17.0")):
            body: EntityDefinition = {"users": users, "groups": groups}
            body["role"] = self.DOWNLOAD_ROLE
            return self.call("remove_role", parameters={self.HREF: href}, body=body)
        else:
            body = {"usernames": users, "groupnames": groups}
            return self.call("remove_permission", parameters={self.HREF: href}, body=body)


class PulpRoleContext(PulpEntityContext):
    ENTITY = _("role")
    ENTITIES = _("roles")
    HREF = "role_href"
    ID_PREFIX = "roles"
    NULLABLES = {"description"}
    NEEDS_PLUGINS = [PluginRequirement("core", "3.17.0")]


class PulpSigningServiceContext(PulpEntityContext):
    ENTITY = _("signing service")
    ENTITIES = _("signing services")
    HREF = "signing_service_href"
    ID_PREFIX = "signing_services"


class PulpTaskContext(PulpEntityContext):
    ENTITY = _("task")
    ENTITIES = _("tasks")
    HREF = "task_href"
    ID_PREFIX = "tasks"
    CAPABILITIES = {"roles": [PluginRequirement("core", "3.17.0")]}

    resource_context: Optional[PulpEntityContext] = None

    def list(self, limit: int, offset: int, parameters: Dict[str, Any]) -> List[Any]:
        if not self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.22.0dev")):
            parameters = parameters.copy()
            reserved_resources = parameters.pop("reserved_resources", None)
            exclusive_resources = parameters.pop("exclusive_resources", None)
            shared_resources = parameters.pop("shared_resources", None)
            parameters.pop("reserved_resources__in", None)
            parameters.pop("exclusive_resources__in", None)
            parameters.pop("shared_resources__in", None)
            reserved_resources_record = []
            if reserved_resources:
                reserved_resources_record.append(reserved_resources)
            if exclusive_resources:
                reserved_resources_record.append(exclusive_resources)
            if shared_resources:
                reserved_resources_record.append("shared:" + shared_resources)
            if len(reserved_resources_record) > 1:
                self.pulp_ctx.needs_plugin(
                    PluginRequirement(
                        "core",
                        min="3.22.0dev",
                        feature=_("specify multiple reserved resources"),
                    ),
                )
            parameters["reserved_resources_record"] = reserved_resources_record

        return super().list(limit=limit, offset=offset, parameters=parameters)

    def cancel(self, task_href: str) -> Any:
        return self.call(
            "cancel",
            parameters={self.HREF: task_href},
            body={"state": "canceled"},
        )

    @property
    def scope(self) -> Dict[str, Any]:
        if self.resource_context:
            if self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.22.0dev")):
                return {"reserved_resources": self.resource_context.pulp_href}
            else:
                return {"reserved_resources_record": [self.resource_context.pulp_href]}
        else:
            return {}

    def purge(
        self,
        finished_before: Optional[datetime.datetime],
        states: Optional[List[str]],
    ) -> Any:
        body: Dict[str, Any] = {}
        if finished_before:
            body["finished_before"] = finished_before
        if states:
            body["states"] = states
        return self.call(
            "purge",
            body=body,
        )

    def summary(self) -> Dict[str, int]:
        task_states = ["waiting", "skipped", "running", "completed", "failed", "canceled"]
        if self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.14.0")):
            task_states.append("canceling")
        result = {}
        for state in task_states:
            payload = {"limit": 1, "state": state}
            result[state] = self.call("list", parameters=payload)["count"]
        return result


class PulpTaskGroupContext(PulpEntityContext):
    ENTITY = _("task group")
    ENTITIES = _("task groups")
    HREF = "task_group_href"
    ID_PREFIX = "task_groups"


class PulpUploadContext(PulpEntityContext):
    ENTITY = _("upload")
    ENTITIES = _("uploads")
    HREF = "upload_href"
    ID_PREFIX = "uploads"

    def upload_chunk(
        self,
        href: str,
        chunk: bytes,
        size: int,
        start: int,
        non_blocking: bool = False,
    ) -> Any:
        end: int = start + len(chunk) - 1
        parameters = {self.HREF: href, "Content-Range": f"bytes {start}-{end}/{size}"}
        return self.call(
            "update",
            parameters=parameters,
            body={"sha256": hashlib.sha256(chunk).hexdigest()},
            uploads={"file": chunk},
            non_blocking=non_blocking,
        )

    def commit(self, upload_href: str, sha256: str) -> Any:
        return self.call(
            "commit",
            parameters={self.HREF: upload_href},
            body={"sha256": sha256},
        )

    def upload_file(self, file: IO[bytes], chunk_size: int = 1000000) -> Any:
        """Upload a file and return the uncommitted upload_href."""
        start = 0
        size = os.path.getsize(file.name)
        upload_href = self.create(body={"size": size})["pulp_href"]
        try:
            self.pulp_href = upload_href
            while start < size:
                chunk = file.read(chunk_size)
                self.upload_chunk(
                    href=upload_href,
                    chunk=chunk,
                    size=size,
                    start=start,
                )
                start += chunk_size
                self.pulp_ctx.echo(".", nl=False, err=True)
        except Exception as e:
            self.delete(upload_href)
            raise e
        self.pulp_ctx.echo(_("Upload complete."), err=True)
        return upload_href


class PulpUserContext(PulpEntityContext):
    ENTITY = _("user")
    ENTITIES = _("users")
    HREF = "auth_user_href"
    ID_PREFIX = "users"
    NULLABLES = {"password"}


class PulpUserRoleContext(PulpEntityContext):
    ENTITY = _("user role")
    ENTITIES = _("user roles")
    HREF = "auth_users_user_role_href"
    ID_PREFIX = "users_roles"
    NULLABLES = {"content_object"}
    user_ctx: PulpUserContext

    def __init__(self, pulp_ctx: PulpContext, user_ctx: PulpUserContext) -> None:
        super().__init__(pulp_ctx)
        self.user_ctx = user_ctx

    @property
    def scope(self) -> Dict[str, Any]:
        return {self.user_ctx.HREF: self.user_ctx.pulp_href}


class PulpWorkerContext(PulpEntityContext):
    ENTITY = _("worker")
    ENTITIES = _("workers")
    HREF = "worker_href"
    ID_PREFIX = "workers"
    HREF_PATTERN = r"workers/"
