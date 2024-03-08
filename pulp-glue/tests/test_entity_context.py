import random
import string
import typing as t

import pytest

from pulp_glue.common.context import PulpContext, PulpRepositoryContext
from pulp_glue.file.context import PulpFileRepositoryContext

pytestmark = pytest.mark.glue


@pytest.fixture
def file_repository(pulp_ctx: PulpContext) -> t.Dict[str, t.Any]:
    name = "".join(random.choices(string.ascii_letters, k=8))
    file_repository_ctx = PulpFileRepositoryContext(pulp_ctx)
    yield file_repository_ctx.create(body={"name": name})
    file_repository_ctx.delete()


def test_detail_context(pulp_ctx: PulpContext, file_repository: t.Dict[str, t.Any]) -> None:
    master_ctx = PulpRepositoryContext(pulp_ctx)
    detail_ctx = master_ctx.detail_context(pulp_href=file_repository["pulp_href"])
    assert isinstance(detail_ctx, PulpFileRepositoryContext)
    assert detail_ctx.entity["name"] == file_repository["name"]
