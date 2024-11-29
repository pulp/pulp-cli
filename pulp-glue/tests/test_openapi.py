import datetime
import json

import pytest

from pulp_glue.common.openapi import OpenAPI, _Response

pytestmark = pytest.mark.glue

TEST_SCHEMA = json.dumps(
    {
        "openapi": "3.0.3",
        "paths": {"test/": {"get": {"operationId": "test_id"}}},
        "components": {"schemas": {}},
    }
).encode()


@pytest.fixture
def openapi(monkeypatch: pytest.MonkeyPatch) -> OpenAPI:
    monkeypatch.setattr(OpenAPI, "load_api", lambda self, refresh_cache: TEST_SCHEMA)
    openapi = OpenAPI("base_url", "doc_path")
    openapi._parse_api(TEST_SCHEMA)
    return openapi


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


def test_extract_params_with_no_match(openapi: OpenAPI) -> None:
    parameters = {"a": 1, "b": "C"}
    query_params = openapi._extract_params("query", {}, {}, parameters)
    assert query_params == {}
    assert parameters == {"a": 1, "b": "C"}


def test_extract_params_raises_for_missing_required_parameter(openapi: OpenAPI) -> None:
    parameters = {"a": 1, "b": "C"}
    with pytest.raises(RuntimeError, match=r"Required parameters \[c\] missing"):
        openapi._extract_params(
            "query",
            {"parameters": [{"name": "c", "in": "query", "required": True}]},
            {},
            parameters,
        )
    assert parameters == {"a": 1, "b": "C"}


def test_extract_params_removes_matches(openapi: OpenAPI) -> None:
    parameters = {"a": 1, "c": "C"}
    query_params = openapi._extract_params(
        "query", {"parameters": [{"name": "c", "in": "query", "required": True}]}, {}, parameters
    )
    assert query_params == {"c": "C"}
    assert parameters == {"a": 1}


def test_extract_params_encodes_date(openapi: OpenAPI) -> None:
    parameters = {"a": datetime.date(2000, 1, 1)}
    query_params = openapi._extract_params(
        "query",
        {
            "parameters": [
                {"name": "a", "in": "query", "schema": {"type": "string", "format": "date"}}
            ]
        },
        {},
        parameters,
    )
    assert query_params == {"a": "2000-01-01"}
