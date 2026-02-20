import asyncio
import datetime
import json
import logging

import pytest
from multidict import CIMultiDict

from pulp_glue.common.authentication import AuthProviderBase, BasicAuthProvider, GlueAuthProvider
from pulp_glue.common.openapi import OpenAPI, _Request, _Response

pytestmark = pytest.mark.glue

SECURITY_SCHEMES = {
    "A": {"type": "http", "scheme": "bearer"},
    "B": {"type": "http", "scheme": "basic"},
    "C": {
        "type": "oauth2",
        "flows": {
            "implicit": {
                "authorizationUrl": "https://example.com/api/oauth/dialog",
                "scopes": {
                    "write:pets": "modify pets in your account",
                    "read:pets": "read your pets",
                },
            },
            "authorizationCode": {
                "authorizationUrl": "https://example.com/api/oauth/dialog",
                "tokenUrl": "https://example.com/api/oauth/token",
                "scopes": {
                    "write:pets": "modify pets in your account",
                    "read:pets": "read your pets",
                },
            },
        },
    },
    "D": {
        "type": "oauth2",
        "flows": {
            "implicit": {
                "authorizationUrl": "https://example.com/api/oauth/dialog",
                "scopes": {
                    "write:pets": "modify pets in your account",
                    "read:pets": "read your pets",
                },
            },
            "clientCredentials": {
                "tokenUrl": "https://example.com/api/oauth/token",
                "scopes": {
                    "write:pets": "modify pets in your account",
                    "read:pets": "read your pets",
                },
            },
        },
    },
    "E": {"type": "mutualTLS"},
}
TEST_SCHEMA = json.dumps(
    {
        "openapi": "3.0.3",
        "paths": {
            "test/": {
                "get": {
                    "operationId": "get_test_id",
                    "responses": {200: {}},
                },
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
                    "security": [{"B": []}],
                },
            }
        },
        "security": [{}],
        "components": {
            "schemas": {
                "testBody": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                }
            },
            "securitySchemes": SECURITY_SCHEMES,
        },
        "info": {
            "title": "test",
            "version": "0.0.0",
        },
    }
).encode()


async def mock_send_request(request: _Request) -> _Response:
    if request.url.endswith("oauth/token"):
        assert request.method.lower() == "post"
        # $ echo -n "client1:secret1" | base64
        assert request.headers["Authorization"] == "Basic Y2xpZW50MTpzZWNyZXQx"
        assert isinstance(request.data, dict)
        assert request.data["grant_type"] == "client_credentials"
        assert set(request.data["scopes"].split(" ")) == {"write:pets", "read:pets"}
        return _Response(
            status_code=200,
            headers={},
            body=json.dumps({"access_token": "DEADBEEF", "expires_in": 600}).encode(),
        )
    else:
        return _Response(status_code=200, headers={}, body=b"{}")


@pytest.fixture
def mock_openapi(monkeypatch: pytest.MonkeyPatch) -> OpenAPI:
    monkeypatch.setattr(OpenAPI, "load_api", lambda self, refresh_cache: TEST_SCHEMA)
    openapi = OpenAPI("base_url", "doc_path", user_agent="test agent")
    openapi._parse_api(TEST_SCHEMA)
    monkeypatch.setattr(openapi, "_send_request", mock_send_request)
    return openapi


@pytest.fixture
def basic_auth_provider(
    monkeypatch: pytest.MonkeyPatch,
    mock_openapi: OpenAPI,
) -> AuthProviderBase:
    auth_provider = BasicAuthProvider(username="user1", password="password1")
    monkeypatch.setattr(mock_openapi, "_auth_provider", auth_provider)
    return auth_provider


@pytest.fixture
def oauth2_cc_auth_provider(
    monkeypatch: pytest.MonkeyPatch,
    mock_openapi: OpenAPI,
) -> AuthProviderBase:
    auth_provider = GlueAuthProvider(client_id="client1", client_secret="secret1")
    monkeypatch.setattr(mock_openapi, "_auth_provider", auth_provider)
    return auth_provider


@pytest.fixture
def tls_auth_provider(
    monkeypatch: pytest.MonkeyPatch,
    mock_openapi: OpenAPI,
) -> AuthProviderBase:
    auth_provider = GlueAuthProvider(cert="asdf")
    monkeypatch.setattr(mock_openapi, "_auth_provider", auth_provider)
    return auth_provider


class TestRenderRequest:
    def test_request_has_no_auth(
        self,
        mock_openapi: OpenAPI,
        basic_auth_provider: AuthProviderBase,
    ) -> None:
        method, path = mock_openapi.operations["get_test_id"]
        path_spec = mock_openapi.api_spec["paths"][path]
        request = mock_openapi._render_request(path_spec, method, "test/", {}, {}, None)
        assert request.security == [{}]

    def test_request_has_security(
        self,
        mock_openapi: OpenAPI,
        basic_auth_provider: AuthProviderBase,
    ) -> None:
        method, path = mock_openapi.operations["post_test_id"]
        path_spec = mock_openapi.api_spec["paths"][path]
        request = mock_openapi._render_request(
            path_spec, method, "test/", {}, {}, {"text": "TRACE"}
        )
        assert request.security == [{"B": []}]


class TestParseResponse:
    def test_returns_dict_for_no_content(
        self,
        mock_openapi: OpenAPI,
    ) -> None:
        response = _Response(204, {}, b"")
        result = mock_openapi._parse_response({}, response)
        assert result == {}

    def test_decodes_json(
        self,
        mock_openapi: OpenAPI,
    ) -> None:
        response = _Response(200, {"content-type": "application/json"}, b'{"a": 1, "b": "Hallo!"}')
        result = mock_openapi._parse_response(
            {"responses": {"200": {"content": {"application/json": {}}}}}, response
        )
        assert result == {"a": 1, "b": "Hallo!"}


class TestExtractParams:
    def test_with_no_match(self, mock_openapi: OpenAPI) -> None:
        parameters = {"a": 1, "b": "C"}
        query_params = mock_openapi._extract_params("query", {}, {}, parameters)
        assert query_params == {}
        assert parameters == {"a": 1, "b": "C"}

    def test_raises_for_missing_required_parameter(self, mock_openapi: OpenAPI) -> None:
        parameters = {"a": 1, "b": "C"}
        with pytest.raises(RuntimeError, match=r"Required parameters \[c\] missing"):
            mock_openapi._extract_params(
                "query",
                {"parameters": [{"name": "c", "in": "query", "required": True}]},
                {},
                parameters,
            )
        assert parameters == {"a": 1, "b": "C"}

    def test_removes_matches(self, mock_openapi: OpenAPI) -> None:
        parameters = {"a": 1, "c": "C"}
        query_params = mock_openapi._extract_params(
            "query",
            {"parameters": [{"name": "c", "in": "query", "required": True}]},
            {},
            parameters,
        )
        assert query_params == {"c": "C"}
        assert parameters == {"a": 1}

    def test_encodes_date(self, mock_openapi: OpenAPI) -> None:
        parameters = {"a": datetime.date(2000, 1, 1)}
        query_params = mock_openapi._extract_params(
            "query",
            {
                "parameters": [
                    {
                        "name": "a",
                        "in": "query",
                        "schema": {"type": "string", "format": "date"},
                    }
                ]
            },
            {},
            parameters,
        )
        assert query_params == {"a": "2000-01-01"}


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


class TestSelectProposal:
    def test_none_if_no_provider(
        self,
        mock_openapi: OpenAPI,
    ) -> None:
        request = _Request(
            "",
            "GET",
            "http://example.org",
            CIMultiDict(),
            security=[{"A": []}, {"B": []}],
        )
        assert mock_openapi._select_proposal(request) is None

    def test_none_if_header_provided(
        self,
        mock_openapi: OpenAPI,
        basic_auth_provider: AuthProviderBase,
    ) -> None:
        request = _Request(
            "",
            "GET",
            "http://example.org",
            CIMultiDict({"Authorization": "Weird Auth"}),
            security=[{"A": []}, {"B": []}],
        )
        assert mock_openapi._select_proposal(request) is None

    def test_B_with_basic_auth(
        self,
        mock_openapi: OpenAPI,
        basic_auth_provider: AuthProviderBase,
    ) -> None:
        request = _Request(
            "",
            "GET",
            "http://example.org",
            CIMultiDict(),
            security=[{"A": []}, {"B": []}],
        )
        assert mock_openapi._select_proposal(request) == {"B": []}

    def test_oauth_with_client_credentials(
        self,
        mock_openapi: OpenAPI,
        oauth2_cc_auth_provider: AuthProviderBase,
    ) -> None:
        request = _Request(
            "",
            "GET",
            "http://example.org",
            CIMultiDict(),
            security=[
                {"A": []},
                {"B": []},
                {"C": []},
                {"D": []},
                {"E": []},
            ],
        )
        assert mock_openapi._select_proposal(request) == {"D": []}

    def test_mutual_tls_with_cert(
        self,
        mock_openapi: OpenAPI,
        tls_auth_provider: AuthProviderBase,
    ) -> None:
        request = _Request(
            "",
            "GET",
            "http://example.org",
            CIMultiDict(),
            security=[
                {"A": []},
                {"B": []},
                {"C": []},
                {"D": []},
                {"E": []},
            ],
        )
        assert mock_openapi._select_proposal(request) == {"E": []}


class TestAuthenticate:
    def test_basic_auth(
        self,
        mock_openapi: OpenAPI,
        basic_auth_provider: AuthProviderBase,
    ) -> None:
        request = _Request("", "GET", "http://example.org", CIMultiDict())
        assert asyncio.run(mock_openapi._authenticate_request(request, {"B": []})) is False
        # $ echo -n "user1:password1" | base64
        assert request.headers.get("Authorization") == "Basic dXNlcjE6cGFzc3dvcmQx"

    def test_tls(
        self,
        mock_openapi: OpenAPI,
        tls_auth_provider: AuthProviderBase,
    ) -> None:
        request = _Request("", "GET", "http://example.org", CIMultiDict())
        assert asyncio.run(mock_openapi._authenticate_request(request, {"E": []})) is False
        # No header, and the certificate is handled by the ssl_context.
        assert "Authorization" not in request.headers

    def test_oauth2_client_credentials(
        self,
        mock_openapi: OpenAPI,
        oauth2_cc_auth_provider: AuthProviderBase,
    ) -> None:
        request = _Request("", "GET", "http://example.org", CIMultiDict())
        assert asyncio.run(mock_openapi._authenticate_request(request, {"D": ["scope1"]})) is False
        assert request.headers.get("Authorization") == "Bearer DEADBEEF"

    def test_oauth2_client_credentials_reuses_token(
        self,
        mock_openapi: OpenAPI,
        oauth2_cc_auth_provider: AuthProviderBase,
    ) -> None:
        mock_openapi._oauth2_token = "BABACAFE"
        mock_openapi._oauth2_expires = datetime.datetime.now() + datetime.timedelta(seconds=500)

        request = _Request("", "GET", "http://example.org", CIMultiDict())
        assert asyncio.run(mock_openapi._authenticate_request(request, {"D": ["scope1"]})) is True
        assert request.headers.get("Authorization") == "Bearer BABACAFE"

    def test_oauth2_client_credentials_refreshes_outdated_token(
        self,
        mock_openapi: OpenAPI,
        oauth2_cc_auth_provider: AuthProviderBase,
    ) -> None:
        mock_openapi._oauth2_token = "BABACAFE"
        mock_openapi._oauth2_expires = datetime.datetime.now() - datetime.timedelta(seconds=500)

        request = _Request("", "GET", "http://example.org", CIMultiDict())
        assert asyncio.run(mock_openapi._authenticate_request(request, {"D": ["scope1"]})) is False
        assert request.headers.get("Authorization") == "Bearer DEADBEEF"
