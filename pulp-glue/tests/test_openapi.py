import pytest

from pulp_glue.common.openapi import OpenAPI, _Response

pytestmark = pytest.mark.glue

TEST_SCHEMA = b'{"openapi": "3.0.3", "paths": {}}'


@pytest.fixture
def openapi(monkeypatch: pytest.MonkeyPatch) -> OpenAPI:
    monkeypatch.setattr(OpenAPI, "_download_api", lambda x: TEST_SCHEMA)
    return OpenAPI("base_url", "doc_path")


def test_parse_response_returns_dict_for_no_content(openapi: OpenAPI) -> None:
    response = _Response(204, {}, b"")
    result = openapi._parse_response({}, response)
    assert result == {}


def test_parse_response_decodes_json(openapi: OpenAPI) -> None:
    response = _Response(200, {"content-type": "application/json"}, b'{"a": 1, "b": "Hallo!"}')
    result = openapi._parse_response(
        {"responses": {"200": {"content": {"application/json": {}}}}}, response
    )
    assert result == {"a": 1, "b": "Hallo!"}
