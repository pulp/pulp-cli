import datetime
import io
import typing as t

import pytest

from pulp_glue.common.schema import SchemaError, ValidationError, transform, encode_json

COMPONENTS = {
    "aString": {"type": "string"},
    "anInteger": {"type": "integer"},
    "aReference": {"$ref": "#/components/schemas/aString"},
    "intArray": {"type": "array", "items": {"type": "integer"}},
    "strArray": {"type": "array", "items": {"$ref": "#/components/schemas/aString"}},
    "minMaxArray": {"type": "array", "minItems": 3, "maxItems": 5, "items": {"type": "integer"}},
    "uniqueArray": {"type": "array", "uniqueItems": True, "items": {"type": "integer"}},
    "unspecifiedObject": {"type": "object"},
    "emptyObject": {"type": "object", "additionalProperties": False},
    "objectAInt": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"a": {"type": "integer"}},
    },
    "objectRequiredA": {
        "type": "object",
        "additionalProperties": {"type": "string"},
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "boolean"},
        },
        "required": ["a"],
    },
    "allOfEnum": {
        "allOf": [
            {"type": "string", "enum": ["a", "b", "c"]},
            {"type": "string", "enum": ["b", "d", "f"]},
        ]
    },
    "anyOfEnum": {
        "anyOf": [
            {"type": "string", "enum": ["a", "b", "c"]},
            {"type": "string", "enum": ["b", "d", "f"]},
        ]
    },
    "allOfCompose": {
        "allOf": [
            {"type": "object", "properties": {"a": {"type": "string", "format": "date"}}},
            {"type": "object", "properties": {"b": {"type": "string", "format": "date"}}},
        ]
    },
}


# This will only pass for identity...
SOME_BYTES = io.BytesIO(b"\000\001\002")


@pytest.mark.parametrize(
    "schema,value,expected",
    [
        pytest.param({}, None, None, id="empty_allows_null"),
        pytest.param({}, "asdf", "asdf", id="empty_allows_string"),
        pytest.param({}, 1, 1, id="empty_allows_int"),
        pytest.param({"nullable": True}, None, None, id="nullable_allows_null"),
        pytest.param(
            {"type": "string", "nullable": True}, None, None, id="typed_nullable_allows_null"
        ),
        pytest.param({"type": "string"}, "asdf", "asdf", id="string"),
        pytest.param(
            {"type": "string", "format": "byte"}, b"\000\001\002", "AAEC", id="string_bytes"
        ),
        pytest.param(
            {"type": "string", "format": "binary"},
            b"\000\001\002",
            b"\000\001\002",
            id="string_binary_allows_bytes",
        ),
        pytest.param(
            {"type": "string", "format": "binary"},
            SOME_BYTES,
            SOME_BYTES,
            id="string_binary_allows_bytestream",
        ),
        pytest.param(
            {"type": "string", "format": "date"},
            datetime.date(2000, 1, 2),
            "2000-01-02",
            id="string_date",
        ),
        pytest.param(
            {"type": "string", "format": "date"},
            datetime.datetime(2000, 1, 2, 12, 1),
            "2000-01-02",
            id="string_date_allows_datetime",
        ),
        pytest.param(
            {"type": "string", "format": "date-time"},
            datetime.datetime(2000, 1, 2, 12, 2),
            "2000-01-02T12:02:00.000000Z",
            id="string_date_allows_datetime",
        ),
        pytest.param(
            {"type": "string", "enum": ["a", "b", "c"]},
            "b",
            "b",
            id="string_enum",
        ),
        pytest.param({"type": "integer"}, 1, 1, id="integer"),
        pytest.param({"type": "integer", "maximum": 10}, 9, 9, id="integer_max"),
        pytest.param(
            {"type": "integer", "exclusiveMaximum": True, "maximum": 10}, 9, 9, id="integer_exmax"
        ),
        pytest.param({"type": "integer", "maximum": 10}, 10, 10, id="integer_max_1"),
        pytest.param({"type": "integer", "minimum": 5}, 6, 6, id="integer_min"),
        pytest.param(
            {"type": "integer", "exclusiveMinimum": True, "minimum": 5}, 6, 6, id="integer_exmin"
        ),
        pytest.param({"type": "integer", "minimum": 5}, 5, 5, id="integer_min_1"),
        pytest.param({"type": "integer", "maximum": 10, "minimum": 5}, 7, 7, id="integer_minmax"),
        pytest.param({"type": "integer", "multipleOf": 7}, 14, 14, id="integer_multiple_of"),
        pytest.param({"type": "boolean"}, False, False, id="boolean_false"),
        pytest.param({"type": "boolean"}, True, True, id="boolean_true"),
        pytest.param({"type": "number"}, 1.5, 1.5, id="number"),
        pytest.param({"type": "number"}, 1.0, 1.0, id="whole_number"),
        pytest.param({"type": "number"}, 1, 1, id="number_allows_integer"),
        pytest.param({"$ref": "#/components/schemas/aString"}, "asdf", "asdf", id="reference"),
        pytest.param(
            {"$ref": "#/components/schemas/aReference"}, "asdf", "asdf", id="double_reference"
        ),
        pytest.param(
            {"$ref": "#/components/schemas/anInteger", "type": "string"},
            1,
            1,
            id="reference_ignores_all_properties",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/intArray"},
            [],
            [],
            id="reference_array",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/intArray"},
            [1, 1, 2, 3, 5],
            [1, 1, 2, 3, 5],
            id="array_of_integer",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/strArray"},
            ["a", "b", "c"],
            ["a", "b", "c"],
            id="array_of_strings",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/minMaxArray"},
            [1, 1, 3],
            [1, 1, 3],
            id="min_max_array",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/unspecifiedObject"},
            {},
            {},
            id="unspecified_object",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/unspecifiedObject"},
            {"a": 1},
            {"a": 1},
            id="unspecified_object_validates_anything",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/emptyObject"},
            {},
            {},
            id="empty_object",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/objectAInt"},
            {"a": 1},
            {"a": 1},
            id="object_with_properties",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/objectRequiredA"},
            {"a": 1},
            {"a": 1},
            id="object_with_required_property",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/allOfEnum"},
            "b",
            "b",
            id="all_of",
        ),
        pytest.param(
            {"allOf": [{"type": "date-time"}], "nullable": True},
            None,
            None,
            id="all_composes_with_current_schema",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/anyOfEnum"},
            "f",
            "f",
            id="any_of_matches_one",
        ),
        pytest.param(
            {"$ref": "#/components/schemas/allOfCompose"},
            {"a": datetime.date(2000, 1, 1), "b": datetime.date(2000, 1, 2)},
            {"a": "2000-01-01", "b": "2000-01-02"},
            id="any_of_matches_one",
        ),
    ],
)
def test_transforms(schema: t.Any, value: t.Any, expected: t.Any) -> None:
    assert transform(schema, "testvar", value, COMPONENTS) == expected


@pytest.mark.parametrize(
    "schema,value",
    [
        pytest.param({"type": "boolean"}, 1, id="boolean_fails_int"),
        pytest.param({"type": "string"}, None, id="string_fails_null"),
        pytest.param({"type": "string"}, 1, id="string_fails_int"),
        pytest.param({"type": "string"}, True, id="string_fails_bool"),
        pytest.param({"type": "string", "nullable": False}, None, id="not_nullable_fails_null"),
        pytest.param({"type": "string", "format": "byte"}, "1234", id="string_bytes_fails_string"),
        pytest.param(
            {"type": "string", "format": "date"},
            "aritrary string",
            id="string_date_fails_string",
        ),
        pytest.param(
            {"type": "string", "enum": ["a", "b", "c"]},
            "d",
            id="string_enum",
        ),
        pytest.param(
            {"type": "integer", "exclusiveMinimum": True, "minimum": 5}, 5, id="integer_exmin"
        ),
        pytest.param(
            {"type": "integer", "exclusiveMaximum": True, "maximum": 5}, 5, id="integer_exmax"
        ),
        pytest.param({"type": "integer", "minimum": 5}, 4, id="integer_min"),
        pytest.param({"type": "integer", "maximum": 5}, 6, id="integer_max"),
        pytest.param({"type": "integer", "multipleOf": 7}, 15, id="integer_multiple_of"),
        pytest.param(
            {"$ref": "#/components/schemas/aString"}, 1, id="string_reference_fails_integer"
        ),
        pytest.param({"type": "number", "minimum": 6.5}, 6.0, id="fails_if_number_is_to_small"),
        pytest.param(
            {"$ref": "#/components/schemas/aReference"},
            1,
            id="double_string_reference_fails_integer",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/intArray",
            },
            True,
            id="array_fails_boolean",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/intArray",
            },
            ["asdf"],
            id="integer_array_fails_string_array",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/strArray",
            },
            ["asdf", False, "ghjk"],
            id="string_array_fails_boolean_in_array",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/minMaxArray",
            },
            [1, 2],
            id="min_max_array_fails_too_small",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/minMaxArray",
            },
            [1, 2, 3, 4, 5, 6],
            id="min_max_array_fails_too_large",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/uniqueArray",
            },
            [1, 2, 1, 6],
            id="unique_array_fails",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/emptyObject",
            },
            [],
            id="object_fails_list",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/emptyObject",
            },
            {"a": 1},
            id="object_fails_non_empty",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/objectAInt",
            },
            {"a": "test"},
            id="object_fails_a_is_wrong_type",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/objectRequiredA",
            },
            {"z": True},
            id="object_fails_required_property_missing",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/objectRequiredA",
            },
            {"a": 1, "z": 2.5},
            id="object_fails_additional_property_not_valid",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/allOfEnum",
            },
            "a",
            id="fails_validate_only_first_all_of",
        ),
        pytest.param(
            {
                "$ref": "#/components/schemas/anyOfEnum",
            },
            "z",
            id="fails_validate_none_matched",
        ),
    ],
)
def test_validation_failed(schema: t.Any, value: t.Any) -> None:
    with pytest.raises(ValidationError, match=r"'testvar.*'"):
        transform(schema, "testvar", value, COMPONENTS)


@pytest.mark.parametrize(
    "schema,value,exc_type",
    [
        pytest.param({"type": "blubb"}, 1, NotImplementedError, id="unknown_type"),
        pytest.param({"$ref": "blubb"}, 1, SchemaError, id="invalid_reference"),
        pytest.param({"$ref": "#/components/schemas/notHere"}, 1, KeyError, id="missing_reference"),
    ],
)
def test_invalid_schema_raises(schema: t.Any, value: t.Any, exc_type: t.Type[Exception]) -> None:
    with pytest.raises(exc_type):
        assert transform(schema, "testvar", value, COMPONENTS)


@pytest.mark.parametrize(
    "obj, output",
    [
        pytest.param(None, "null", id="null"),
        pytest.param(1, "1", id="integer"),
        pytest.param(datetime.date(1970, 1, 1), '"1970-01-01"'),
        pytest.param(datetime.datetime(1970, 1, 1, 12), '"1970-01-01T12:00:00.000000Z"'),
    ],
)
def test_json_encoder(obj: t.Any, output: str) -> None:
    assert encode_json(obj) == output


def test_json_encoder_rejects_binary() -> None:
    with pytest.raises(TypeError):
        encode_json({"a": b"asdf"})


def test_json_encoder_rejects_stream() -> None:
    with pytest.raises(TypeError):
        encode_json({"a": SOME_BYTES})
