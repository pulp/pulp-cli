import typing as t

from pulp_glue.common.context import PulpEntityContext
from pulp_glue.common.i18n import get_translation

translation = get_translation(__package__)
_ = translation.gettext


class PulpMigrationPlanContext(PulpEntityContext):
    ENTITY = _("pulp_2to3_migration_migration_plan")
    HREF = "pulp_2to3_migration_migration_plan_href"
    ID_PREFIX = "migration_plans"

    def run(self, href: t.Optional[str] = None) -> t.Any:
        return self.pulp_ctx.call(
            "migration_plans_run", parameters={self.HREF: href or self.pulp_href}
        )

    def reset(self, href: t.Optional[str] = None) -> t.Any:
        return self.pulp_ctx.call(
            "migration_plans_reset", parameters={self.HREF: href or self.pulp_href}
        )


class PulpMigrationPulp2ContentContext(PulpEntityContext):
    ENTITY = _("pulp_2to3_migration_pulp2_content")
    HREF = "pulp_2to3_migration_pulp2_content_href"
    ID_PREFIX = "pulp2content"


class PulpMigrationPulp2RepositoryContext(PulpEntityContext):
    ENTITY = _("pulp_2to3_migration_pulp2_repository")
    HREF = "pulp_2to3_migration_pulp2_repository_href"
    ID_PREFIX = "pulp2repositories"
