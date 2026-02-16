import typing as t

import pydantic
import pytest

from pulp_glue.common.pydantic_oas import (
    OpenAPISpec,
    Parameter,
    SchemaParameter,
    SecuritySchemeHttp,
)

pytestmark = pytest.mark.glue


SECURITY_SCHEMES: dict[str, dict[str, t.Any]] = {
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

TEST_SCHEMA = {
    "openapi": "3.1.1",
    "info": {
        "title": "Test API",
        "version": "3.141592653",
        "license": {
            "name": "Creative Commons Zero v1.0 Universal",
            "identifier": "CC0-1.0",
        },
        "x-this-is-something": True,
    },
    "paths": {
        "test/": {
            "get": {
                "operationId": "get_test_id",
                "parameters": [
                    {
                        "name": "sort",
                        "in": "query",
                        "content": {"text/plain": {"schema": {}, "encoding": {}}},
                    },
                    {"name": "gingerbread", "in": "cookie", "schema": {}},
                ],
                "responses": {"200": {"description": "SUCCESS"}},
            },
            "post": {
                "operationId": "post_test_id",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/testBody"}}
                    },
                },
                "responses": {"200": {"description": "SUCCESS"}},
                "security": [{"B": []}],
            },
            "parameters": [{"$ref": "#/components/parameters/query1"}],
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
        "parameters": {
            "query1": {"name": "query1", "in": "query", "schema": {}},
        },
        "securitySchemes": SECURITY_SCHEMES,
    },
}

ParameterAdapter = pydantic.TypeAdapter[Parameter](Parameter)


class TestPydanticOpenAPISpec:
    def test_validate(self) -> None:
        spec = OpenAPISpec.model_validate(TEST_SCHEMA)
        assert spec.components is not None
        assert spec.components.security_schemes is not None
        assert isinstance(spec.components.security_schemes["A"], SecuritySchemeHttp)
        assert spec.paths is not None
        assert spec.paths["test/"].get is not None
        assert spec.paths["test/"].get.parameters is not None
        assert isinstance(spec.paths["test/"].get.parameters[0], Parameter)
        assert spec.paths["test/"].get.parameters[0].in_ == "query"

    @pytest.mark.skip
    def test_validate_with_context_enumerates_operations(self) -> None:
        operations: dict[str, tuple[str, str]] = {}
        OpenAPISpec.model_validate(TEST_SCHEMA, context={"path": "", "operations": operations})
        assert operations["get_test_id"] == ("test/", "get")

    def test_path_parameter_is_required(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            ParameterAdapter.validate_python(
                {"in": "path", "name": "cannotbeoptional", "schema": {}}
            )
        with pytest.raises(pydantic.ValidationError):
            ParameterAdapter.validate_python(
                {
                    "in": "path",
                    "name": "cannotbeoptional",
                    "required": False,
                    "schema": {},
                }
            )

    @pytest.mark.parametrize(
        "in_,style",
        (
            ("query", "form"),
            ("path", "simple"),
            ("header", "simple"),
            ("cookie", "form"),
        ),
    )
    def test_parameter_style_defaults_to(self, in_: str, style: str) -> None:
        parameter = ParameterAdapter.validate_python(
            {"in": in_, "name": "test", "required": True, "schema": {}}
        )
        assert isinstance(parameter, SchemaParameter)
        assert parameter.style == style

    @pytest.mark.parametrize(
        "style,explode",
        (
            ("simple", False),
            ("form", True),
            ("matrix", False),
            ("label", False),
            ("spaceDelimited", False),
            ("pipeDelimited", False),
            ("deepObject", False),
        ),
    )
    def test_parameter_explode_defautls_to(self, style: str, explode: bool) -> None:
        parameter = ParameterAdapter.validate_python(
            {
                "in": "query",
                "name": "test",
                "required": True,
                "style": style,
                "schema": {},
            }
        )
        assert isinstance(parameter, SchemaParameter)
        assert parameter.explode == explode
