import json
import typing as t

import pytest

from pulp_glue.common import context as context_module
from pulp_glue.common.context import PulpContext, PulpDistributionContext
from pulp_glue.common.exceptions import PulpException
from pulp_glue.common.openapi import OpenAPI
from pulp_glue.file.context import PulpFileDistributionContext
from pulp_glue.rpm.context import PulpRpmDistributionContext

pytestmark = pytest.mark.glue

REPO_HREF = "/pulp/api/v3/repositories/rpm/rpm/01234567-0123-0123-0123-0123456789ab/"
REPO_VERSION_HREF = REPO_HREF + "versions/5/"
PUBLICATION_HREF = "/pulp/api/v3/publications/rpm/rpm/01234567-0123-0123-0123-0123456789ab/"


@pytest.fixture
def modern_pulp_ctx(monkeypatch: pytest.MonkeyPatch) -> PulpContext:
    spec = json.dumps(
        {
            "openapi": "3.0.3",
            "info": {
                "title": "test",
                "version": "0.0.0",
                "x-pulp-app-versions": {"core": "3.106.0", "rpm": "3.30.0", "file": "3.75.0"},
            },
            "paths": {},
        }
    )
    monkeypatch.setattr(context_module, "_patch_api_hook", lambda spec: spec)
    monkeypatch.setattr(OpenAPI, "load_api", lambda self, refresh_cache: self._parse_api(spec))
    monkeypatch.setattr(
        OpenAPI,
        "_send_request",
        lambda *args, **kwargs: pytest.fail("No API calls allowed in unit tests."),
    )
    settings: dict[str, t.Any] = {"base_url": "nowhere"}
    return PulpContext.from_config(settings)


@pytest.mark.parametrize(
    "ctx_cls",
    [PulpRpmDistributionContext, PulpFileDistributionContext],
    ids=["rpm", "file"],
)
class TestDistributionPreprocess:
    def test_version_with_repository(
        self, modern_pulp_ctx: PulpContext, ctx_cls: type[PulpDistributionContext]
    ) -> None:
        ctx = ctx_cls(modern_pulp_ctx)
        body = ctx.preprocess_entity({"version": 5, "repository": REPO_HREF}, partial=False)
        assert body["repository_version"] == REPO_VERSION_HREF
        assert body["repository"] is None
        assert body["publication"] is None
        assert "version" not in body

    def test_repository_without_version(
        self, modern_pulp_ctx: PulpContext, ctx_cls: type[PulpDistributionContext]
    ) -> None:
        ctx = ctx_cls(modern_pulp_ctx)
        body = ctx.preprocess_entity({"repository": REPO_HREF}, partial=False)
        assert body["repository"] == REPO_HREF
        assert body["repository_version"] is None
        assert body["publication"] is None

    def test_publication_without_repository(
        self, modern_pulp_ctx: PulpContext, ctx_cls: type[PulpDistributionContext]
    ) -> None:
        ctx = ctx_cls(modern_pulp_ctx)
        body = ctx.preprocess_entity({"publication": PUBLICATION_HREF}, partial=False)
        assert body["publication"] == PUBLICATION_HREF
        assert body["repository"] is None
        assert body["repository_version"] is None

    def test_version_without_repository_raises(
        self, modern_pulp_ctx: PulpContext, ctx_cls: type[PulpDistributionContext]
    ) -> None:
        ctx = ctx_cls(modern_pulp_ctx)
        with pytest.raises(PulpException, match="--repository"):
            ctx.preprocess_entity({"version": 5}, partial=False)

    def test_version_without_repository_partial_raises(
        self, modern_pulp_ctx: PulpContext, ctx_cls: type[PulpDistributionContext]
    ) -> None:
        ctx = ctx_cls(modern_pulp_ctx)
        ctx._entity = {"repository": None, "repository_version": None}
        with pytest.raises(PulpException, match="--repository"):
            ctx.preprocess_entity({"version": 5}, partial=True)

    def test_partial_version_infers_repository(
        self, modern_pulp_ctx: PulpContext, ctx_cls: type[PulpDistributionContext]
    ) -> None:
        ctx = ctx_cls(modern_pulp_ctx)
        ctx._entity = {"repository": REPO_HREF, "repository_version": None}
        body = ctx.preprocess_entity({"version": 3}, partial=True)
        assert body["repository_version"] == REPO_HREF + "versions/3/"
        assert body["repository"] is None
        assert body["publication"] is None

    def test_unrelated_field_no_nullification(
        self, modern_pulp_ctx: PulpContext, ctx_cls: type[PulpDistributionContext]
    ) -> None:
        ctx = ctx_cls(modern_pulp_ctx)
        body = ctx.preprocess_entity({"base_path": "/new/path"}, partial=True)
        assert body.get("base_path") == "/new/path"
        assert "repository" not in body
        assert "repository_version" not in body
        assert "publication" not in body
