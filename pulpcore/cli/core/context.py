from typing import Any, ClassVar, Dict, IO, Optional
import hashlib
import os
import sys
import click

from pulpcore.cli.common.context import (
    EntityData,
    PulpContext,
    PulpEntityContext,
)


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
    UPDATE_ID = "exporters_core_pulp_update"
    DELETE_ID = "exporters_core_pulp_delete"


class PulpExportContext(PulpEntityContext):
    ENTITY = "PulpExport"
    HREF = "pulp_pulp_export_href"
    LIST_ID = "exporters_core_pulp_exports_list"
    READ_ID = "exporters_core_pulp_exports_read"
    CREATE_ID = "exporters_core_pulp_exports_create"
    DELETE_ID = "exporters_core_pulp_exports_delete"

    def __new__(cls, pulp_ctx: PulpContext) -> Any:
        if not pulp_ctx.has_plugin("pulpcore", min_version="3.10.dev0"):
            # Workaround for improperly rendered nested resource paths and weird HREF names
            # https://github.com/pulp/pulpcore/pull/1066
            class PatchedPulpExporterContext(PulpExportContext):
                HREF = "core_pulp_pulp_export_href"

                def create(
                    self, body: EntityData, parameters: Optional[Dict[str, Any]] = None
                ) -> Any:
                    if parameters and PulpExporterContext.HREF in parameters:
                        parameters[self.HREF] = parameters.pop(PulpExporterContext.HREF)
                    return super().create(parameters=parameters, body=body)

            return super().__new__(PatchedPulpExporterContext)
        return super().__new__(cls)


class PulpGroupContext(PulpEntityContext):
    ENTITY = "group"
    HREF = "auth_group_href"
    LIST_ID = "groups_list"
    READ_ID = "groups_read"
    CREATE_ID = "groups_create"
    UPDATE_ID = "groups_update"
    DELETE_ID = "groups_delete"

    def find(self, **kwargs: Any) -> Any:
        """Workaroud for the missing ability to filter"""
        if self.pulp_ctx.has_plugin("pulpcore", min_version="3.10"):
            # Workaround not needed anymore
            return super().find(**kwargs)
        # See https://pulp.plan.io/issues/7975
        search_result = self.list(limit=sys.maxsize, offset=0, parameters={})
        for key, value in kwargs.items():
            search_result = [res for res in search_result if res[key] == value]
        if len(search_result) != 1:
            raise click.ClickException(f"Could not find {self.ENTITY} with {kwargs}.")
        return search_result[0]


class PulpImporterContext(PulpEntityContext):
    ENTITY = "PulpImporter"
    HREF = "pulp_importer_href"
    CREATE_ID = "importers_core_pulp_create"
    READ_ID = "importers_core_pulp_read"
    UPDATE_ID = "importers_core_pulp_update"
    DELETE_ID = "importers_core_pulp_delete"
    LIST_ID = "importers_core_pulp_list"


class PulpTaskContext(PulpEntityContext):
    ENTITY = "task"
    HREF = "task_href"
    LIST_ID = "tasks_list"
    READ_ID = "tasks_read"
    CANCEL_ID: ClassVar[str] = "tasks_cancel"

    def cancel(self, task_href: str) -> Any:
        return self.pulp_ctx.call(
            self.CANCEL_ID,
            parameters={self.HREF: task_href},
            body={"state": "canceled"},
        )


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
        if self.pulp_ctx.has_plugin("pulpcore", min_version="3.10"):
            # Workaround not needed anymore
            return super().find(**kwargs)
        # See https://pulp.plan.io/issues/7975
        search_result = self.list(limit=sys.maxsize, offset=0, parameters={})
        for key, value in kwargs.items():
            search_result = [res for res in search_result if res[key] == value]
        if len(search_result) != 1:
            raise click.ClickException(f"Could not find {self.ENTITY} with {kwargs}.")
        return search_result[0]
