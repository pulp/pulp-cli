import json
import logging
import typing as t

import pytest

from pulp_glue.common.openapi import OpenAPI

TEST_SCHEMA = json.dumps(
    {
        "openapi": "3.0.3",
        "paths": {"test/": {"get": {"operationId": "test_id", "responses": {200: {}}}}},
        "components": {"schemas": {}},
    }
).encode()


class MockRequest:
    headers: t.Dict[str, str] = {}
    body: t.Dict[str, t.Any] = {}


class MockResponse:
    status_code = 200
    headers: t.Dict[str, str] = {}
    text = "{}"
    content: t.Dict[str, t.Any] = {}

    def raise_for_status(self) -> None:
        pass


class MockSession:
    def prepare_request(self, *args: t.Any, **kwargs: t.Any) -> MockRequest:
        return MockRequest()

    def send(self, request: MockRequest) -> MockResponse:
        return MockResponse()


@pytest.fixture
def openapi(monkeypatch: pytest.MonkeyPatch) -> OpenAPI:
    monkeypatch.setattr(OpenAPI, "load_api", lambda self, refresh_cache: TEST_SCHEMA)
    openapi = OpenAPI("base_url", "doc_path")
    openapi._parse_api(TEST_SCHEMA)
    monkeypatch.setattr(openapi, "_session", MockSession())
    return openapi


def test_openapi_logs_nothing_from_info(openapi: OpenAPI, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    openapi.call("test_id")
    assert caplog.record_tuples == []


def test_openapi_logs_operation_info_to_debug(
    openapi: OpenAPI, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    openapi.call("test_id")
    assert caplog.record_tuples == [
        ("pulp_glue.openapi", logging.DEBUG + 3, "test_id : get test/"),
        ("pulp_glue.openapi", logging.DEBUG + 2, ""),
        ("pulp_glue.openapi", logging.DEBUG + 1, "{}"),
        ("pulp_glue.openapi", logging.DEBUG + 3, "Response: 200"),
        ("pulp_glue.openapi", logging.DEBUG + 1, "{}"),
    ]
