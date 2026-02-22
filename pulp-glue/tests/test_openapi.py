import asyncio
import datetime
import json
import logging
import typing as t

import pytest
from multidict import CIMultiDict

from pulp_glue.common.authentication import (
    AuthProviderBase,
    BasicAuthProvider,
    GlueAuthProvider,
)
from pulp_glue.common.exceptions import ValidationError
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
        "openapi": "3.1.1",
        "paths": {
            "test/": {
                "get": {
                    "operationId": "get_test_id",
                    "responses": {200: {"description": "get test"}},
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
                    "responses": {200: {"description": "post test"}},
                    "security": [{"B": []}],
                },
            },
            "render_params/": {
                "head": {
                    "operationId": "render_params_ref",
                    "parameters": [{"$ref": "#/components/parameters/limit"}],
                },
                "get": {
                    "operationId": "render_params_none",
                },
                "trace": {
                    "operationId": "render_params_query",
                    "parameters": [
                        {"name": "query1", "in": "query", "schema": {"type": "string"}},
                        {"name": "query2", "in": "query", "schema": {"type": "string"}},
                        {
                            "name": "date",
                            "in": "query",
                            "schema": {"type": "string", "format": "date"},
                        },
                    ],
                },
                "delete": {
                    "operationId": "render_params_lists",
                    "parameters": [
                        {
                            "name": "qlist",
                            "in": "query",
                            "explode": False,
                            "schema": {"type": "array", "items": {"type": "string"}},
                        },
                        {
                            "name": "hlist",
                            "in": "header",
                            "schema": {"type": "array", "items": {"type": "string"}},
                        },
                        {
                            "name": "clist",
                            "in": "cookie",
                            "explode": False,
                            "schema": {"type": "array", "items": {"type": "string"}},
                        },
                        {
                            "name": "eqlist",
                            "in": "query",
                            "schema": {"type": "array", "items": {"type": "string"}},
                        },
                        {
                            "name": "ehlist",
                            "in": "header",
                            "explode": True,
                            "schema": {"type": "array", "items": {"type": "string"}},
                        },
                        {
                            "name": "eclist",
                            "in": "cookie",
                            "schema": {"type": "array", "items": {"type": "string"}},
                        },
                    ],
                },
            },
            "render_params/{pk}/": {
                "head": {
                    "operationId": "render_params_pk_query",
                    "parameters": [
                        {"name": "query1", "in": "query", "schema": {"type": "string"}},
                        {"name": "query2", "in": "query", "schema": {"type": "string"}},
                    ],
                },
                "get": {
                    "operationId": "render_params_pk_",
                },
                "parameters": [
                    {
                        "name": "pk",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    },
                ],
            },
        },
        "security": [{}],
        "components": {
            "parameters": {
                "limit": {"name": "limit", "in": "query", "schema": {"type": "int"}},
            },
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


def mock_send_request(request: _Request) -> _Response:
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
    monkeypatch.setattr(
        OpenAPI, "load_api", lambda self, refresh_cache: self._parse_api(TEST_SCHEMA)
    )
    openapi = OpenAPI("base_url", "doc_path", user_agent="test agent")
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
        path_spec = mock_openapi._api_spec.paths[path]
        request = mock_openapi._render_request(path_spec, method, "test/", {}, {}, None)
        assert request.security == [{}]

    def test_request_has_security(
        self,
        mock_openapi: OpenAPI,
        basic_auth_provider: AuthProviderBase,
    ) -> None:
        method, path = mock_openapi.operations["post_test_id"]
        path_spec = mock_openapi._api_spec.paths[path]
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


class TestRenderParameters:
    @pytest.mark.parametrize(
        "operation_id,parameters,match",
        (
            pytest.param(
                "render_params_none",
                {"superfluous": "1234"},
                r"superfluous",
                id="remaining_parameters",
            ),
            pytest.param(
                "render_params_pk_query",
                {"query1": "asdf"},
                r"pk",
                id="missing_required_parameter",
            ),
            pytest.param(
                "render_params_query",
                {"query1": "asdf", "query2": 35},
                r"query2",
                id="wrong_type",
            ),
        ),
    )
    def test_fails_validation_for(
        self,
        mock_openapi: OpenAPI,
        operation_id: str,
        parameters: dict[str, t.Any],
        match: str,
    ) -> None:
        method, path = mock_openapi.operations[operation_id]
        path_spec = mock_openapi._api_spec.paths[path]
        method_spec = getattr(path_spec, method)

        with pytest.raises(ValidationError, match=match):
            mock_openapi._render_parameters(path_spec, method_spec, parameters)

    def test_references_are_not_implemented(self, mock_openapi: OpenAPI) -> None:
        parameters: dict[str, t.Any] = {}
        method, path = mock_openapi.operations["render_params_ref"]
        path_spec = mock_openapi._api_spec.paths[path]
        method_spec = getattr(path_spec, method)

        with pytest.raises(NotImplementedError):
            mock_openapi._render_parameters(path_spec, method_spec, parameters)

        assert parameters == {}

    def test_no_parameters_none_specified(self, mock_openapi: OpenAPI) -> None:
        parameters: dict[str, t.Any] = {}
        method, path = mock_openapi.operations["render_params_none"]
        path_spec = mock_openapi._api_spec.paths[path]
        method_spec = getattr(path_spec, method)

        res = mock_openapi._render_parameters(path_spec, method_spec, parameters)

        assert res == {"query": {}, "header": {}, "path": {}, "cookie": {}}
        assert parameters == {}

    def test_provided_parameters_are_rendered(self, mock_openapi: OpenAPI) -> None:
        parameters: dict[str, t.Any] = {"query1": "asdf", "pk": 42}
        method, path = mock_openapi.operations["render_params_pk_query"]
        path_spec = mock_openapi._api_spec.paths[path]
        method_spec = getattr(path_spec, method)

        res = mock_openapi._render_parameters(path_spec, method_spec, parameters)

        assert res == {
            "query": {"query1": "asdf"},
            "header": {},
            "path": {"pk": 42},
            "cookie": {},
        }
        assert parameters == {"query1": "asdf", "pk": 42}

    def test_lists_are_rendered_according_to_explode(self, mock_openapi: OpenAPI) -> None:
        parameters: dict[str, t.Any] = {
            "qlist": ["1", "2", "3"],
            "eqlist": ["1", "2", "3"],
            "hlist": ["1", "2", "3"],
            "ehlist": ["1", "2", "3"],
            "clist": ["1", "2", "3"],
            "eclist": ["1", "2", "3"],
        }
        method, path = mock_openapi.operations["render_params_lists"]
        path_spec = mock_openapi._api_spec.paths[path]
        method_spec = getattr(path_spec, method)

        res = mock_openapi._render_parameters(path_spec, method_spec, parameters)

        assert res == {
            "query": {"qlist": "1,2,3", "eqlist": ["1", "2", "3"]},
            "header": {"hlist": "1,2,3", "ehlist": ["1", "2", "3"]},
            "path": {},
            "cookie": {"clist": "1,2,3", "eclist": ["1", "2", "3"]},
        }

    def test_encodes_date(self, mock_openapi: OpenAPI) -> None:
        parameters = {"date": datetime.date(2000, 1, 1)}
        method, path = mock_openapi.operations["render_params_query"]
        path_spec = mock_openapi._api_spec.paths[path]
        method_spec = getattr(path_spec, method)

        res = mock_openapi._render_parameters(path_spec, method_spec, parameters)
        assert res["query"] == {"date": "2000-01-01"}


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
