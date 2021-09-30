import gettext
import hashlib
import os
import sys
from typing import IO, Any, ClassVar, Dict, List, Optional

import click

from pulpcore.cli.common.context import EntityDefinition, PulpContext, PulpEntityContext

_ = gettext.gettext


class PulpAccessPolicyContext(PulpEntityContext):
    ENTITY = _("access policy")
    ENTITIES = _("access policies")
    HREF = "access_policy_href"
    LIST_ID = "access_policies_list"
    READ_ID = "access_policies_read"
    UPDATE_ID = "access_policies_partial_update"


class PulpArtifactContext(PulpEntityContext):
    ENTITY = _("artifact")
    ENTITIES = _("artifacts")
    HREF = "artifact_href"
    LIST_ID = "artifacts_list"
    READ_ID = "artifacts_read"
    CREATE_ID = "artifacts_create"

    def upload(self, file: IO[bytes], chunk_size: int = 1000000) -> Any:
        upload_ctx = PulpUploadContext(self.pulp_ctx)
        start = 0
        size = os.path.getsize(file.name)

        sha256 = hashlib.sha256()
        for chunk in iter(lambda: file.read(chunk_size), b""):
            sha256.update(chunk)
        sha256_digest = sha256.hexdigest()
        file.seek(0)

        # check whether the file exists before uploading
        result = self.list(limit=1, offset=0, parameters={"sha256": sha256_digest})
        if len(result) > 0:
            click.echo(_("Artifact already exists."), err=True)
            return result[0]["pulp_href"]

        click.echo(_("Uploading file {filename}").format(filename=file.name), err=True)

        if chunk_size > size:
            # if chunk_size is bigger than the file size, just upload it directly
            artifact: Dict[str, Any] = self.create(
                {"sha256": sha256_digest}, uploads={"file": file.read()}
            )
            return artifact["pulp_href"]

        upload_href = upload_ctx.create(body={"size": size})["pulp_href"]

        try:
            while start < size:
                end = min(size, start + chunk_size) - 1
                file.seek(start)
                chunk = file.read(chunk_size)
                range_header = f"bytes {start}-{end}/{size}"
                upload_ctx.update(
                    href=upload_href,
                    parameters={"Content-Range": range_header},
                    body={"sha256": hashlib.sha256(chunk).hexdigest()},
                    uploads={"file": chunk},
                )
                start += chunk_size
                click.echo(".", nl=False, err=True)

            click.echo(_("Upload complete. Creating artifact."), err=True)
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
    LIST_ID = "exporters_core_pulp_list"
    READ_ID = "exporters_core_pulp_read"
    CREATE_ID = "exporters_core_pulp_create"
    UPDATE_ID = "exporters_core_pulp_partial_update"
    DELETE_ID = "exporters_core_pulp_delete"


class PulpExportContext(PulpEntityContext):
    ENTITY = _("Pulp export")
    ENTITIES = _("Pulp exports")
    HREF = "pulp_pulp_export_href"
    LIST_ID = "exporters_core_pulp_exports_list"
    READ_ID = "exporters_core_pulp_exports_read"
    CREATE_ID = "exporters_core_pulp_exports_create"
    DELETE_ID = "exporters_core_pulp_exports_delete"
    exporter: EntityDefinition

    @property
    def scope(self) -> Dict[str, Any]:
        return {PulpExporterContext.HREF: self.exporter["pulp_href"]}


class PulpGroupContext(PulpEntityContext):
    ENTITY = _("user group")
    ENTITIES = _("user groups")
    HREF = "auth_group_href"
    LIST_ID = "groups_list"
    READ_ID = "groups_read"
    CREATE_ID = "groups_create"
    UPDATE_ID = "groups_partial_update"
    DELETE_ID = "groups_delete"


class PulpGroupPermissionContext(PulpEntityContext):
    ENTITY = _("group permission")
    ENTITIES = _("group permissions")
    group_ctx: PulpGroupContext

    def __init__(self, pulp_ctx: PulpContext, group_ctx: PulpGroupContext) -> None:
        super().__init__(pulp_ctx)
        self.group_ctx = group_ctx

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
            raise click.ClickException(
                _("Could not find {entity} with {kwargs}.").format(
                    entity=self.ENTITY, kwargs=kwargs
                )
            )
        return search_result[0]

    @property
    def scope(self) -> Dict[str, Any]:
        return {PulpGroupContext.HREF: self.group_ctx.pulp_href}


class PulpGroupModelPermissionContext(PulpGroupPermissionContext):
    ENTITY = _("group model permission")
    ENTITIES = _("group model permissions")
    HREF = "auth_groups_model_permission_href"
    LIST_ID = "groups_model_permissions_list"
    READ_ID = "groups_model_permissions_read"
    CREATE_ID = "groups_model_permissions_create"
    DELETE_ID = "groups_model_permissions_delete"


class PulpGroupObjectPermissionContext(PulpGroupPermissionContext):
    ENTITY = _("group object permission")
    ENTITIES = _("group object permissions")
    HREF = "auth_groups_object_permission_href"
    LIST_ID = "groups_object_permissions_list"
    READ_ID = "groups_object_permissions_read"
    CREATE_ID = "groups_object_permissions_create"
    DELETE_ID = "groups_object_permissions_delete"


class PulpGroupUserContext(PulpEntityContext):
    ENTITY = _("group user")
    ENTITIES = _("group users")
    HREF = "auth_groups_user_href"
    LIST_ID = "groups_users_list"
    CREATE_ID = "groups_users_create"
    DELETE_ID = "groups_users_delete"
    group_ctx: PulpGroupContext

    def __init__(self, pulp_ctx: PulpContext, group_ctx: PulpGroupContext) -> None:
        super().__init__(pulp_ctx)
        self.group_ctx = group_ctx

    @property
    def scope(self) -> Dict[str, Any]:
        return {PulpGroupContext.HREF: self.group_ctx.pulp_href}


class PulpContentGuardContext(PulpEntityContext):
    ENTITY = "content guard"
    ENTITIES = "content guards"
    HREF_PATTERN = r"^/pulp/api/v3/contentguards/(?P<plugin>\w+)/(?P<resource_type>\w+)/"
    LIST_ID = "contentguards_list"


class PulpImporterContext(PulpEntityContext):
    ENTITY = _("Pulp importer")
    ENTITIES = _("Pulp importers")
    HREF = "pulp_importer_href"
    CREATE_ID = "importers_core_pulp_create"
    READ_ID = "importers_core_pulp_read"
    UPDATE_ID = "importers_core_pulp_partial_update"
    DELETE_ID = "importers_core_pulp_delete"
    LIST_ID = "importers_core_pulp_list"


class PulpRbacContentGuardContext(PulpContentGuardContext):
    ENTITY = "RBAC content guard"
    ENTITIES = "RBAC content guards"
    HREF = "r_b_a_c_content_guard_href"
    LIST_ID = "contentguards_core_rbac_list"
    CREATE_ID = "contentguards_core_rbac_create"
    UPDATE_ID = "contentguards_core_rbac_partial_update"
    DELETE_ID = "contentguards_core_rbac_delete"
    READ_ID = "contentguards_core_rbac_read"
    ASSIGN_ID: ClassVar[str] = "contentguards_core_rbac_assign_permission"
    REMOVE_ID: ClassVar[str] = "contentguards_core_rbac_remove_permission"

    def assign(self, href: str, users: Optional[List[str]], groups: Optional[List[str]]) -> Any:
        body = self.preprocess_body({"usernames": users, "groupnames": groups})
        return self.pulp_ctx.call(self.ASSIGN_ID, parameters={self.HREF: href}, body=body)

    def remove(self, href: str, users: Optional[List[str]], groups: Optional[List[str]]) -> Any:
        body = self.preprocess_body({"usernames": users, "groupnames": groups})
        return self.pulp_ctx.call(self.REMOVE_ID, parameters={self.HREF: href}, body=body)


class PulpSigningServiceContext(PulpEntityContext):
    ENTITY = _("signing service")
    ENTITIES = _("signing services")
    HREF = "signing_service_href"
    LIST_ID = "signing_services_list"
    READ_ID = "signing_services_read"


class PulpTaskContext(PulpEntityContext):
    ENTITY = _("task")
    ENTITIES = _("tasks")
    HREF = "task_href"
    LIST_ID = "tasks_list"
    READ_ID = "tasks_read"
    DELETE_ID = "tasks_delete"
    CANCEL_ID: ClassVar[str] = "tasks_cancel"

    resource_context: Optional[PulpEntityContext] = None

    def cancel(self, task_href: str) -> Any:
        return self.pulp_ctx.call(
            self.CANCEL_ID,
            parameters={self.HREF: task_href},
            body={"state": "canceled"},
        )

    @property
    def scope(self) -> Dict[str, Any]:
        if self.resource_context:
            return {"reserved_resources_record": self.resource_context.pulp_href}
        else:
            return {}


class PulpTaskGroupContext(PulpEntityContext):
    ENTITY = _("task group")
    ENTITIES = _("task groups")
    HREF = "task_group_href"
    LIST_ID = "task_groups_list"
    READ_ID = "task_groups_read"


class PulpUploadContext(PulpEntityContext):
    ENTITY = _("upload")
    ENTITIES = _("uploads")
    HREF = "upload_href"
    LIST_ID = "uploads_list"
    READ_ID = "uploads_read"
    CREATE_ID = "uploads_create"
    UPDATE_ID = "uploads_update"
    DELETE_ID = "uploads_delete"
    COMMIT_ID: ClassVar[str] = "uploads_commit"

    def commit(self, upload_href: str, sha256: str) -> Any:
        return self.pulp_ctx.call(
            self.COMMIT_ID,
            parameters={self.HREF: upload_href},
            body={"sha256": sha256},
        )


class PulpUserContext(PulpEntityContext):
    ENTITY = _("user")
    ENTITIES = _("users")
    HREF = "auth_user_href"
    LIST_ID = "users_list"
    READ_ID = "users_read"


class PulpWorkerContext(PulpEntityContext):
    ENTITY = _("worker")
    ENTITIES = _("workers")
    HREF = "worker_href"
    LIST_ID = "workers_list"
    READ_ID = "workers_read"
