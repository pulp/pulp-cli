from typing import Any

from pulpcore.cli.common.context import PulpEntityContext


class PulpMigrationPlanContext(PulpEntityContext):
    ENTITY = "pulp_2to3_migration_migration_plan"
    HREF = "pulp_2to3_migration_migration_plan_href"
    LIST_ID = "migration_plans_list"
    READ_ID = "migration_plans_read"
    CREATE_ID = "migration_plans_create"
    UPDATE_ID = "migration_plans_partial_update"
    DELETE_ID = "migration_plans_delete"

    def run(self, href: str) -> Any:
        return self.pulp_ctx.call("migration_plans_run", parameters={self.HREF: href})

    def reset(self, href: str) -> Any:
        return self.pulp_ctx.call("migration_plans_reset", parameters={self.HREF: href})


class PulpMigrationPulp2ContentContext(PulpEntityContext):
    ENTITY = "pulp_2to3_migration_pulp2_content"
    HREF = "pulp_2to3_migration_pulp2_content_href"
    LIST_ID = "pulp2content_list"
    READ_ID = "pulp2content_read"


class PulpMigrationPulp2RepositoryContext(PulpEntityContext):
    ENTITY = "pulp_2to3_migration_pulp2_repository"
    HREF = "pulp_2to3_migration_pulp2_repository_href"
    LIST_ID = "pulp2repositories_list"
    READ_ID = "pulp2repositories_read"
