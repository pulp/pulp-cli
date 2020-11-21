from typing import Any, ClassVar

import click

from pulpcore.cli.common.context import (
    PulpEntityContext,
)


class PulpArtifactContext(PulpEntityContext):
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

    def delete(self, name: str) -> Any:
        the_exporter = self.find(name=name)
        return super().delete(the_exporter["pulp_href"])


class PulpExportContext(PulpEntityContext):
    ENTITY = "PulpExport"
    HREF = "core_pulp_pulp_export_href"
    LIST_ID = "exporters_core_pulp_exports_list"
    READ_ID = "exporters_core_pulp_exports_read"
    CREATE_ID = "exporters_core_pulp_exports_create"
    DELETE_ID = "exporters_core_pulp_exports_delete"
    EXPORTER_LIST_ID: ClassVar[str] = "exporters_core_pulp_list"

    def find_exporter(self, name: str) -> Any:
        search_result = self.pulp_ctx.call(
            self.EXPORTER_LIST_ID, parameters={"name": name, "limit": 1}
        )
        if search_result["count"] != 1:
            raise click.ClickException(f"PulpExporter '{name}' not found.")
        exporter = search_result["results"][0]
        return exporter


class PulpTaskContext(PulpEntityContext):
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
