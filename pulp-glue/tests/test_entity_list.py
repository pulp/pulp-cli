import random
import string
import typing as t

import pytest

from pulp_glue.common.context import PulpContext
from pulp_glue.file.context import PulpFileRepositoryContext

pytestmark = pytest.mark.glue


@pytest.fixture
def file_repository(pulp_ctx: PulpContext) -> t.Iterator[t.Dict[str, t.Any]]:
    name = "".join(random.choices(string.ascii_letters, k=8))
    file_repository_ctx = PulpFileRepositoryContext(pulp_ctx)
    yield file_repository_ctx.create(body={"name": name})
    file_repository_ctx.delete()


@pytest.mark.live
def test_entity_list(pulp_ctx: PulpContext, file_repository: t.Dict[str, t.Any]) -> None:
    entity_ctx = PulpFileRepositoryContext(pulp_ctx)
    assert (
        len(entity_ctx.list(limit=1, offset=0, parameters={"name": file_repository["name"]})) == 1
    )


@pytest.mark.live
def test_entity_list_iterator(pulp_ctx: PulpContext, file_repository: t.Dict[str, t.Any]) -> None:
    entity_ctx = PulpFileRepositoryContext(pulp_ctx)
    stats: t.Dict[str, t.Any] = {}
    assert (
        len(
            list(
                entity_ctx.list_iterator(parameters={"name": file_repository["name"]}, stats=stats)
            )
        )
        == 1
    )
    assert stats["count"] == 1
