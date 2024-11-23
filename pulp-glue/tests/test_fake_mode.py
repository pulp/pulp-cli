import random
import string
import typing as t

import pytest

from pulp_glue.common.context import PulpContext
from pulp_glue.common.exceptions import NotImplementedFake
from pulp_glue.file.context import PulpFileRepositoryContext

pytestmark = pytest.mark.glue


@pytest.fixture
def file_repository(pulp_ctx: PulpContext) -> t.Iterator[t.Dict[str, t.Any]]:
    name = "".join(random.choices(string.ascii_letters, k=8))
    repository_ctx = PulpFileRepositoryContext(pulp_ctx)
    yield repository_ctx.create(body={"name": name})
    repository_ctx.delete()


@pytest.mark.live
def test_fake_status(fake_pulp_ctx: PulpContext) -> None:
    fake_pulp_ctx.call("status_read")


@pytest.mark.live
def test_fake_repository_read(fake_pulp_ctx: PulpContext) -> None:
    repository_ctx = PulpFileRepositoryContext(fake_pulp_ctx)
    repository_ctx.list(limit=0, offset=0, parameters={})


@pytest.mark.live
def test_fake_repository_create(fake_pulp_ctx: PulpContext) -> None:
    name = "".join(random.choices(string.ascii_letters, k=8))
    repository_ctx = PulpFileRepositoryContext(fake_pulp_ctx)
    result = repository_ctx.create(body={"name": name})
    assert result["name"] == name
    assert result["pulp_href"] == "<FAKE ENTITY>"


@pytest.mark.live
def test_fake_repository_update(
    fake_pulp_ctx: PulpContext, file_repository: t.Dict[str, t.Any]
) -> None:
    repository_ctx = PulpFileRepositoryContext(
        fake_pulp_ctx, pulp_href=file_repository["pulp_href"]
    )
    result = repository_ctx.update(body={"description": "TEST"})
    assert result["pulp_href"] == file_repository["pulp_href"]
    assert result["name"] == file_repository["name"]
    assert result["description"] == "TEST"

    # Reload from server
    repository_ctx.pulp_href = file_repository["pulp_href"]
    repository_ctx.entity == file_repository


@pytest.mark.live
def test_fake_repository_delete(
    fake_pulp_ctx: PulpContext, file_repository: t.Dict[str, t.Any]
) -> None:
    repository_ctx = PulpFileRepositoryContext(
        fake_pulp_ctx, pulp_href=file_repository["pulp_href"]
    )
    result = repository_ctx.delete()
    assert result is None

    # Reload from server
    repository_ctx.pulp_href = file_repository["pulp_href"]
    repository_ctx.entity == file_repository


@pytest.mark.live
def test_fake_raises(fake_pulp_ctx: PulpContext) -> None:
    name = "".join(random.choices(string.ascii_letters, k=8))
    with pytest.raises(NotImplementedFake):
        fake_pulp_ctx.call("repositories_file_file_create", body={"name": name})
