import pytest

from pulp_glue.common.context import PulpContext, PulpEntityContext
from pulp_glue.common.exceptions import ValidationError
from pulp_glue.core.context import PulpTaskContext, PulpUploadContext
from pulp_glue.file.context import PulpFileRemoteContext

pytestmarks = pytest.mark.glue


class TestPRNRouting:
    @pytest.mark.parametrize(
        "prn,exc_pattern",
        (
            pytest.param("not_a_prn", r"[Nn]ot.*PRN", id="invalid string"),
            pytest.param(
                "prn:file.filerepository:01234567-0123-0123-012-30123456789ab",
                r"[Nn]ot.*PRN",
                id="invalid uuid",
            ),
            pytest.param(
                "prn:not_a_plugin.filerepository:01234567-0123-0123-0123-0123456789ab",
                r"unknown",
                id="unknown plugin",
            ),
            pytest.param(
                "prn:file.not_a_resource:01234567-0123-0123-0123-0123456789ab",
                r"unknown",
                id="unknown resource type",
            ),
        ),
    )
    def test_fails_if(self, mock_pulp_ctx: PulpContext, prn: str, exc_pattern: str) -> None:
        with pytest.raises(ValidationError, match=exc_pattern):
            mock_pulp_ctx.resolve_prn(prn)

    @pytest.mark.parametrize(
        "prn,ctx_class,pulp_href",
        (
            pytest.param(
                "prn:core.upload:01234567-0123-0123-0123-0123456789ab",
                PulpUploadContext,
                "/api/v3/uploads/01234567-0123-0123-0123-0123456789ab/",
                id="upload",
            ),
            pytest.param(
                "prn:core.task:01234567-0123-0123-0123-0123456789ab",
                PulpTaskContext,
                "/api/v3/tasks/01234567-0123-0123-0123-0123456789ab/",
                id="task",
            ),
            pytest.param(
                "prn:file.fileremote:01234567-0123-0123-0123-0123456789ab",
                PulpFileRemoteContext,
                "/api/v3/remotes/file/file/01234567-0123-0123-0123-0123456789ab/",
                id="file_remote",
            ),
        ),
    )
    def test_returns_entity_context_with_href(
        self,
        mock_pulp_ctx: PulpContext,
        prn: str,
        ctx_class: type[PulpEntityContext],
        pulp_href: str,
    ) -> None:
        entity_ctx = mock_pulp_ctx.resolve_prn(prn)

        assert isinstance(entity_ctx, ctx_class)
        assert entity_ctx._entity_lookup["pulp_href"].endswith(pulp_href)
