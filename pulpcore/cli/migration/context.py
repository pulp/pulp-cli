from typing import Any

from pulpcore.cli.common.context import PulpEntityContext
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


class PulpMigrationPlanContext(PulpEntityContext):
    ENTITY = _("pulp_2to3_migration_migration_plan")
    HREF = "pulp_2to3_migration_migration_plan_href"
    ID_PREFIX = "migration_plans"

    def run(self, href: str) -> Any:
        return self.pulp_ctx.call("migration_plans_run", parameters={self.HREF: href})

    def reset(self, href: str) -> Any:
        return self.pulp_ctx.call("migration_plans_reset", parameters={self.HREF: href})


class PulpMigrationPulp2ContentContext(PulpEntityContext):
    ENTITY = _("pulp_2to3_migration_pulp2_content")
    HREF = "pulp_2to3_migration_pulp2_content_href"
    ID_PREFIX = "pulp2content"


class PulpMigrationPulp2RepositoryContext(PulpEntityContext):
    ENTITY = _("pulp_2to3_migration_pulp2_repository")
    HREF = "pulp_2to3_migration_pulp2_repository_href"
    ID_PREFIX = "pulp2repositories"
