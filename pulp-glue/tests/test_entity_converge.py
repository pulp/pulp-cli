import random
import string
import typing as t

import pytest

from pulp_glue.common.context import PulpContext
from pulp_glue.file.context import PulpFileRemoteContext, PulpFileRepositoryContext

pytestmark = pytest.mark.glue


@pytest.fixture
def file_remote(pulp_ctx: PulpContext) -> t.Dict[str, t.Any]:
    name = "".join(random.choices(string.ascii_letters, k=8))
    file_remote_ctx = PulpFileRemoteContext(pulp_ctx)
    yield file_remote_ctx.create(body={"name": name, "url": "https://localhost/"})
    file_remote_ctx.delete()


@pytest.fixture
def file_repository(pulp_ctx: PulpContext) -> t.Dict[str, t.Any]:
    name = "".join(random.choices(string.ascii_letters, k=8))
    file_repository_ctx = PulpFileRepositoryContext(pulp_ctx)
    yield file_repository_ctx.create(body={"name": name})
    file_repository_ctx.delete()


def test_converge_crud(pulp_ctx: PulpContext) -> None:
    name = "".join(random.choices(string.ascii_letters, k=8))
    description = "".join(random.choices(string.ascii_letters, k=8))
    entity_ctx = PulpFileRepositoryContext(pulp_ctx, entity={"name": name})
    assert entity_ctx.converge({}) is True

    entity_ctx.entity = {"name": name}
    assert entity_ctx.converge({}) is False

    entity_ctx.entity = {"name": name}
    assert entity_ctx.converge({"description": description}) is True

    entity_ctx.entity = {"name": name}
    assert entity_ctx.converge({"description": description}) is False

    entity_ctx.entity = {"name": name}
    assert entity_ctx.converge({"description": ""}) is True

    entity_ctx.entity = {"name": name}
    assert entity_ctx.converge({"description": ""}) is False

    entity_ctx.entity = {"name": name}
    assert entity_ctx.converge(None) is True

    entity_ctx.entity = {"name": name}
    assert entity_ctx.converge(None) is False


def test_converge_linked_object(
    pulp_ctx: PulpContext, file_repository: t.Dict[str, t.Any], file_remote: t.Dict[str, t.Any]
) -> None:
    name = file_repository["name"]
    entity_ctx = PulpFileRepositoryContext(pulp_ctx, entity={"name": name})
    assert entity_ctx.converge({"remote": file_remote["pulp_href"]}) is True

    entity_ctx.entity = {"name": name}
    assert entity_ctx.converge({"remote": file_remote["pulp_href"]}) is False

    entity_ctx.entity = {"name": name}
    remote_ctx = PulpFileRemoteContext(pulp_ctx, entity={"name": file_remote["name"]})
    assert entity_ctx.converge({"remote": remote_ctx}) is False

    entity_ctx.entity = {"name": name}
    assert entity_ctx.converge({"remote": ""}) is True

    entity_ctx.entity = {"name": name}
    assert entity_ctx.converge({"remote": ""}) is False


def test_converge_href(pulp_ctx: PulpContext, file_repository: t.Dict[str, t.Any]) -> None:
    entity_ctx = PulpFileRepositoryContext(pulp_ctx, pulp_href=file_repository["pulp_href"])
    assert entity_ctx.converge({}) is False

    entity_ctx.pulp_href = entity_ctx.pulp_href
    assert entity_ctx.converge({"description": "Test converge on repository."}) is True

    entity_ctx.pulp_href = entity_ctx.pulp_href
    assert entity_ctx.converge({"description": "Test converge on repository."}) is False

    entity_ctx.pulp_href = entity_ctx.pulp_href
    assert entity_ctx.entity["description"] == "Test converge on repository."
