from typing import Any, ClassVar

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


class PulpExportContext(PulpEntityContext):
    ENTITY = "PulpExport"
    HREF = "core_pulp_pulp_export_href"
    LIST_ID = "exporters_core_pulp_exports_list"
    READ_ID = "exporters_core_pulp_exports_read"
    CREATE_ID = "exporters_core_pulp_exports_create"
    DELETE_ID = "exporters_core_pulp_exports_delete"


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
