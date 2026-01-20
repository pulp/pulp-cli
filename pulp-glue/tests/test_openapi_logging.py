import json
import logging

import pytest

from pulp_glue.common.openapi import OpenAPI, _Request, _Response

pytestmark = pytest.mark.glue

TEST_SCHEMA = json.dumps(
    {
        "openapi": "3.0.3",
        "paths": {
            "test/": {
                "get": {"operationId": "get_test_id", "responses": {200: {}}},
                "post": {
                    "operationId": "post_test_id",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/testBody"}
                            }
                        },
                    },
                    "responses": {200: {}},
                },
            }
        },
        "components": {
            "schemas": {
                "testBody": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                }
            }
        },
    }
).encode()


def mock_send_request(request: _Request) -> _Response:
    return _Response(status_code=200, headers={}, body=b"{}")


@pytest.fixture
def mock_openapi(monkeypatch: pytest.MonkeyPatch) -> OpenAPI:
    monkeypatch.setattr(OpenAPI, "load_api", lambda self, refresh_cache: TEST_SCHEMA)
    openapi = OpenAPI("base_url", "doc_path", user_agent="test agent")
    openapi._parse_api(TEST_SCHEMA)
    monkeypatch.setattr(
        openapi,
        "_send_request",
        mock_send_request,
    )
    return openapi


class TestOpenAPILogs:
    def test_nothing_with_level_info(
        self,
        mock_openapi: OpenAPI,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO)
        mock_openapi.call("get_test_id")
        assert caplog.record_tuples == []

    def test_get_operation_to_debug(
        self,
        mock_openapi: OpenAPI,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.DEBUG, logger="pulp_glue.openapi")
        mock_openapi.call("get_test_id")
        assert caplog.record_tuples == [
            ("pulp_glue.openapi", logging.DEBUG + 3, "get_test_id : get test/"),
            ("pulp_glue.openapi", logging.DEBUG + 2, "  User-Agent: test agent"),
            ("pulp_glue.openapi", logging.DEBUG + 2, "  Accept: application/json"),
            ("pulp_glue.openapi", logging.DEBUG + 3, "Response: 200"),
            ("pulp_glue.openapi", logging.DEBUG + 1, "b'{}'"),
        ]

    def test_post_operation_to_debug(
        self,
        mock_openapi: OpenAPI,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.DEBUG, logger="pulp_glue.openapi")
        mock_openapi.call("post_test_id", body={"text": "Trace"})
        assert caplog.record_tuples == [
            ("pulp_glue.openapi", logging.DEBUG + 3, "post_test_id : post test/"),
            ("pulp_glue.openapi", logging.DEBUG + 2, "  User-Agent: test agent"),
            ("pulp_glue.openapi", logging.DEBUG + 2, "  Accept: application/json"),
            (
                "pulp_glue.openapi",
                logging.DEBUG + 2,
                "  Content-Type: application/json",
            ),
            ("pulp_glue.openapi", logging.DEBUG + 1, '\'{"text": "Trace"}\''),
            ("pulp_glue.openapi", logging.DEBUG + 3, "Response: 200"),
            ("pulp_glue.openapi", logging.DEBUG + 1, "b'{}'"),
        ]
