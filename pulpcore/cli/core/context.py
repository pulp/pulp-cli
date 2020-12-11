from typing import Any, ClassVar
import sys
import click

from pulpcore.cli.common.context import (
    PulpEntityContext,
)


class PulpArtifactContext(PulpEntityContext):
    ENTITY = "artifact"
    HREF = "artifact_href"
    LIST_ID = "artifacts_list"
    READ_ID = "artifacts_read"


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
    HREF = "core_pulp_pulp_export_href"
    LIST_ID = "exporters_core_pulp_exports_list"
    READ_ID = "exporters_core_pulp_exports_read"
    CREATE_ID = "exporters_core_pulp_exports_create"
    DELETE_ID = "exporters_core_pulp_exports_delete"


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
