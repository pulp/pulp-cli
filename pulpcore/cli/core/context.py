import gettext
import hashlib
import os
import sys
from typing import IO, Any, ClassVar, Dict, List, Optional

import click

from pulpcore.cli.common.context import EntityDefinition, PulpContext, PulpEntityContext

_ = gettext.gettext


class PulpAccessPolicyContext(PulpEntityContext):
    ENTITY = "access policy"
    ENTITIES = "access_policies"
    HREF = "access_policy_href"
    LIST_ID = "access_policies_list"
    READ_ID = "access_policies_read"
    UPDATE_ID = "access_policies_partial_update"

    def find(self, **kwargs: Any) -> Any:
        """Workaroud for the missing ability to filter"""
        # https://pulp.plan.io/issues/8189
        if self.pulp_ctx.has_plugin("core", min_version="3.10.dev"):
            # Workaround not needed anymore
            return super().find(**kwargs)
        search_result = self.list(limit=sys.maxsize, offset=0, parameters={})
        for key, value in kwargs.items():
            search_result = [res for res in search_result if res[key] == value]
        if len(search_result) != 1:
            raise click.ClickException(f"Could not find {self.ENTITY} with {kwargs}.")
        return search_result[0]


class PulpArtifactContext(PulpEntityContext):
    ENTITY = "artifact"
    HREF = "artifact_href"
    LIST_ID = "artifacts_list"
    READ_ID = "artifacts_read"

    def upload(self, file: IO[bytes], chunk_size: int = 1000000, check_exists: bool = True) -> Any:
        upload_ctx = PulpUploadContext(self.pulp_ctx)
        start = 0
        size = os.path.getsize(file.name)
        sha256 = hashlib.sha256()

        if check_exists:
            for chunk in iter(lambda: file.read(chunk_size), b""):
                sha256.update(chunk)
            result = self.list(limit=1, offset=0, parameters={"sha256": sha256.hexdigest()})
            if len(result) > 0:
                click.echo("Artifact already exists.", err=True)
                return result[0]["pulp_href"]

        click.echo(f"Uploading file {file.name}", err=True)
        upload_href = upload_ctx.create(body={"size": size})["pulp_href"]

        try:
            while start < size:
                end = min(size, start + chunk_size) - 1
                file.seek(start)
                chunk = file.read(chunk_size)
                if not check_exists:
                    sha256.update(chunk)
                range_header = f"bytes {start}-{end}/{size}"
                upload_ctx.update(
                    href=upload_href,
                    parameters={"Content-Range": range_header},
                    body={"sha256": hashlib.sha256(chunk).hexdigest()},
                    uploads={"file": chunk},
                )
                start += chunk_size
                click.echo(".", nl=False, err=True)

            click.echo("Upload complete. Creating artifact.", err=True)
            task = upload_ctx.commit(
                upload_href,
                sha256.hexdigest(),
            )
            result = task["created_resources"][0]
        except Exception as e:
            upload_ctx.delete(upload_href)
            raise e
        return result


class PulpExporterContext(PulpEntityContext):
    ENTITY = "PulpExporter"
    HREF = "pulp_exporter_href"
    LIST_ID = "exporters_core_pulp_list"
    READ_ID = "exporters_core_pulp_read"
    CREATE_ID = "exporters_core_pulp_create"
    UPDATE_ID = "exporters_core_pulp_partial_update"
    DELETE_ID = "exporters_core_pulp_delete"


class PulpExportContext(PulpEntityContext):
    ENTITY = "PulpExport"
    # This is replaced by a version aware property below
    # HREF = "pulp_pulp_export_href"
    LIST_ID = "exporters_core_pulp_exports_list"
    READ_ID = "exporters_core_pulp_exports_read"
    CREATE_ID = "exporters_core_pulp_exports_create"
    DELETE_ID = "exporters_core_pulp_exports_delete"
    exporter: EntityDefinition

    def list(self, limit: int, offset: int, parameters: Dict[str, Any]) -> List[Any]:
        if not self.pulp_ctx.has_plugin("core", min_version="3.10.dev"):
            # Workaround for improperly rendered nested resource paths and weird HREF names
            # https://github.com/pulp/pulpcore/pull/1066
            parameters[PulpExporterContext.HREF] = self.exporter["pulp_href"]
        return super().list(limit=limit, offset=offset, parameters=parameters)

    def create(
        self,
        body: EntityDefinition,
        parameters: Optional[Dict[str, Any]] = None,
        non_blocking: bool = False,
    ) -> Any:
        if not self.pulp_ctx.has_plugin("core", min_version="3.10.dev"):
            # Workaround for improperly rendered nested resource paths and weird HREF names
            # https://github.com/pulp/pulpcore/pull/1066
            if parameters is None:
                parameters = {}
            parameters[self.HREF] = self.exporter["pulp_href"]
        return super().create(parameters=parameters, body=body, non_blocking=non_blocking)

    @property
    def HREF(self) -> str:  # type: ignore
        if not self.pulp_ctx.has_plugin("core", min_version="3.10.dev"):
            # Workaround for improperly rendered nested resource paths and weird HREF names
            # https://github.com/pulp/pulpcore/pull/1066
            return "core_pulp_pulp_export_href"
        return "pulp_pulp_export_href"

    @property
    def scope(self) -> Dict[str, Any]:
        if not self.pulp_ctx.has_plugin("core", min_version="3.10.dev"):
            # Workaround for improperly rendered nested resource paths and weird HREF names
            # https://github.com/pulp/pulpcore/pull/1066
            return {}
        return {PulpExporterContext.HREF: self.exporter["pulp_href"]}


class PulpGroupContext(PulpEntityContext):
    ENTITY = "group"
    HREF = "auth_group_href"
    LIST_ID = "groups_list"
    READ_ID = "groups_read"
    CREATE_ID = "groups_create"
    UPDATE_ID = "groups_partial_update"
    DELETE_ID = "groups_delete"

    def find(self, **kwargs: Any) -> Any:
        """Workaroud for the missing ability to filter"""
        if self.pulp_ctx.has_plugin("core", min_version="3.10.dev"):
            # Workaround not needed anymore
            return super().find(**kwargs)
        # See https://pulp.plan.io/issues/7975
        search_result = self.list(limit=sys.maxsize, offset=0, parameters={})
        for key, value in kwargs.items():
            search_result = [res for res in search_result if res[key] == value]
        if len(search_result) != 1:
            raise click.ClickException(f"Could not find {self.ENTITY} with {kwargs}.")
        return search_result[0]


class PulpGroupPermissionContext(PulpEntityContext):
    ENTITY = "group permission"
    ENTITIES = "group permissions"
    group_ctx: PulpGroupContext

    def __init__(self, pulp_ctx: PulpContext, group_ctx: PulpGroupContext) -> None:
        pulp_ctx.needs_plugin("core", min_version="3.10.dev")
        super().__init__(pulp_ctx)
        self.group_ctx = group_ctx

    def find(self, **kwargs: Any) -> Any:
        """Workaroud for the missing ability to filter"""
        # # TODO fix upstream and adjust to guard for the proper version
        # # https://pulp.plan.io/issues/8241
        # if self.pulp_ctx.has_plugin("core", min_version="3.99.dev"):
        #     # Workaround not needed anymore
        #     return super().find(**kwargs)
        search_result = self.list(limit=sys.maxsize, offset=0, parameters={})
        for key, value in kwargs.items():
            search_result = [res for res in search_result if res[key] == value]
        if len(search_result) != 1:
            raise click.ClickException(f"Could not find {self.ENTITY} with {kwargs}.")
        return search_result[0]

    @property
    def scope(self) -> Dict[str, Any]:
        return {PulpGroupContext.HREF: self.group_ctx.pulp_href}


class PulpGroupModelPermissionContext(PulpGroupPermissionContext):
    ENTITY = "group model permission"
    ENTITIES = "group model permissions"
    HREF = "auth_groups_model_permission_href"
    LIST_ID = "groups_model_permissions_list"
    READ_ID = "groups_model_permissions_read"
    CREATE_ID = "groups_model_permissions_create"
    DELETE_ID = "groups_model_permissions_delete"


class PulpGroupObjectPermissionContext(PulpGroupPermissionContext):
    ENTITY = "group object permission"
    ENTITIES = "group object permissions"
    HREF = "auth_groups_object_permission_href"
    LIST_ID = "groups_object_permissions_list"
    READ_ID = "groups_object_permissions_read"
    CREATE_ID = "groups_object_permissions_create"
    DELETE_ID = "groups_object_permissions_delete"


class PulpGroupUserContext(PulpEntityContext):
    ENTITY = "group user"
    # This is replaced by a version aware property below
    # HREF = "auth_groups_user_href"
    LIST_ID = "groups_users_list"
    CREATE_ID = "groups_users_create"
    DELETE_ID = "groups_users_delete"
    group_ctx: PulpGroupContext

    def __init__(self, pulp_ctx: PulpContext, group_ctx: PulpGroupContext) -> None:
        super().__init__(pulp_ctx)
        self.group_ctx = group_ctx

    def list(self, limit: int, offset: int, parameters: Dict[str, Any]) -> List[Any]:
        if not self.pulp_ctx.has_plugin("core", min_version="3.10.dev"):
            # Workaround for improperly rendered nested resource paths and weird HREF names
            # https://github.com/pulp/pulpcore/pull/1066
            parameters[PulpGroupContext.HREF] = self.group_ctx.pulp_href
        return super().list(limit=limit, offset=offset, parameters=parameters)

    def create(
        self,
        body: EntityDefinition,
        parameters: Optional[Dict[str, Any]] = None,
        non_blocking: bool = False,
    ) -> Any:
        if not self.pulp_ctx.has_plugin("core", min_version="3.10.dev"):
            # Workaround for improperly rendered nested resource paths and weird HREF names
            # https://github.com/pulp/pulpcore/pull/1066
            if parameters is None:
                parameters = {}
            parameters[self.HREF] = self.group_ctx.pulp_href
        return super().create(parameters=parameters, body=body, non_blocking=non_blocking)

    @property
    def HREF(self) -> str:  # type: ignore
        if not self.pulp_ctx.has_plugin("core", min_version="3.10.dev"):
            # Workaround for improperly rendered nested resource paths and weird HREF names
            # https://github.com/pulp/pulpcore/pull/1066
            return "auth_auth_groups_user_href"
        return "auth_groups_user_href"

    @property
    def scope(self) -> Dict[str, Any]:
        if not self.pulp_ctx.has_plugin("core", min_version="3.10.dev"):
            # Workaround for improperly rendered nested resource paths and weird HREF names
            # https://github.com/pulp/pulpcore/pull/1066
            return {}
        return {PulpGroupContext.HREF: self.group_ctx.pulp_href}


class PulpImporterContext(PulpEntityContext):
    ENTITY = "PulpImporter"
    HREF = "pulp_importer_href"
    CREATE_ID = "importers_core_pulp_create"
    READ_ID = "importers_core_pulp_read"
    UPDATE_ID = "importers_core_pulp_partial_update"
    DELETE_ID = "importers_core_pulp_delete"
    LIST_ID = "importers_core_pulp_list"


class PulpSigningServiceContext(PulpEntityContext):
    ENTITY = "signing service"
    ENTITIES = "signing services"
    HREF = "signing_service_href"
    LIST_ID = "signing_services_list"
    READ_ID = "signing_services_read"


class PulpTaskContext(PulpEntityContext):
    ENTITY = "task"
    HREF = "task_href"
    LIST_ID = "tasks_list"
    READ_ID = "tasks_read"
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
    ENTITY = "task group"
    HREF = "task_group_href"
    LIST_ID = "task_groups_list"
    READ_ID = "task_groups_read"


class PulpUploadContext(PulpEntityContext):
    ENTITY = "upload"
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
    ENTITY = "user"
    HREF = "auth_user_href"
    LIST_ID = "users_list"
    READ_ID = "users_read"

    def find(self, **kwargs: Any) -> Any:
        """Workaroud for the missing ability to filter"""
        if self.pulp_ctx.has_plugin("core", min_version="3.10.dev"):
            # Workaround not needed anymore
            return super().find(**kwargs)
        # See https://pulp.plan.io/issues/7975
        search_result = self.list(limit=sys.maxsize, offset=0, parameters={})
        for key, value in kwargs.items():
            search_result = [res for res in search_result if res[key] == value]
        if len(search_result) != 1:
            raise click.ClickException(f"Could not find {self.ENTITY} with {kwargs}.")
        return search_result[0]


class PulpWorkerContext(PulpEntityContext):
    ENTITY = "worker"
    HREF = "worker_href"
    LIST_ID = "workers_list"
    READ_ID = "workers_read"
