import base64
import datetime
import io
import json
import typing as t
from contextlib import suppress

from pulp_glue.common.i18n import get_translation

translation = get_translation(__package__)
_ = translation.gettext

ISO_DATE_FORMAT = "%Y-%m-%d"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class SchemaError(ValueError):
    pass


class ValidationError(ValueError):
    pass


class OpenApi3JsonEncoder(json.JSONEncoder):
    def default(self, o: t.Any) -> t.Any:
        if isinstance(o, datetime.datetime):
            return o.strftime(ISO_DATETIME_FORMAT)
        elif isinstance(o, datetime.date):
            return o.strftime(ISO_DATE_FORMAT)
        else:
            return super().default(o)


def encode_json(o: t.Any) -> str:
    return json.dumps(o, cls=OpenApi3JsonEncoder)


def _assert_type(
    name: str,
    value: t.Any,
    types: t.Union[t.Type[object], t.Tuple[t.Type[object], ...]],
    type_name: str,
) -> None:
    if not isinstance(value, types):
        raise ValidationError(
            _("'{name}' is expected to be a {type_name}.").format(name=name, type_name=type_name)
        )


def _assert_min_max(schema: t.Any, name: str, value: t.Any) -> None:
    if (minimum := schema.get("minimum")) is not None:
        if schema.get("exclusiveMinimum", False):
            if minimum >= value:
                raise ValidationError(
                    _("'{name}' is expected to be larger than {minimum}").format(
                        name=name, minimum=minimum
                    )
                )
        else:
            if minimum > value:
                raise ValidationError(
                    _("'{name}' is expected to not be smaller than {minimum}").format(
                        name=name, minimum=minimum
                    )
                )
    if (maximum := schema.get("maximum")) is not None:
        if schema.get("exclusiveMaximum", False):
            if maximum <= value:
                raise ValidationError(
                    _("'{name}' is expected to be smaller than {maximum}").format(
                        name=name, maximum=maximum
                    )
                )
        else:
            if maximum < value:
                raise ValidationError(
                    _("'{name}' is expected to not be larger than {maximum}").format(
                        name=name, maximum=maximum
                    )
                )


def transform(schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]) -> t.Any:
    if (schema_ref := schema.get("$ref")) is not None:
        # From json-schema:
        # "All other properties in a "$ref" object MUST be ignored."
        return transform_ref(schema_ref, name, value, components)

    if value is None:
        if schema.get("nullable", False):
            return None

    if (schema_type := schema.get("type")) is not None:
        if (typed_transform := _TYPED_TRANSFORMS.get(schema_type)) is not None:
            value = typed_transform(schema, name, value, components)
        else:
            raise NotImplementedError(
                _("Type `{schema_type}` is not implemented yet.").format(schema_type=schema_type)
            )

    # allOf etc allow for composition, but the spec isn't particularly clear about that.
    if (all_of := schema.get("allOf")) is not None:
        if isinstance(value, dict):
            value = value.copy()
            for sub_schema in all_of:
                value = transform(sub_schema, name, value, components)
        else:
            # This may not even be a valid case according to the specification.
            # But it is used by drf-spectacular to reference enum-strings.
            value = [transform(sub_schema, name, value, components) for sub_schema in all_of][0]

    if (any_of := schema.get("anyOf")) is not None:
        for sub_schema in any_of:
            with suppress(ValidationError):
                value = transform(sub_schema, name, value, components)
                break
        else:
            raise ValidationError(
                _("'{name}' does not match any of the provide schemata.").format(name=name)
            )
    return value


def transform_ref(
    schema_ref: str, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> t.Any:
    if not schema_ref.startswith("#/components/schemas/"):
        raise SchemaError(_("'{name}' contains an invalid reference.").format(name=name))
    schema_name = schema_ref[21:]
    return transform(components[schema_name], name, value, components)


def transform_array(
    schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> t.Any:
    _assert_type(name, value, list, "array")
    if (min_items := schema.get("minItems")) is not None:
        if len(value) < min_items:
            raise ValidationError(
                _("'{name}' is expected to have at least {min_items} items.").format(
                    name=name, min_items=min_items
                )
            )
    if (max_items := schema.get("maxItems")) is not None:
        if len(value) > max_items:
            raise ValidationError(
                _("'{name}' is expected to have at most {max_items} items.").format(
                    name=name, max_items=max_items
                )
            )
    if schema.get("uniqueItems", False):
        if len(set(value)) != len(value):
            raise ValidationError(_("'{name}' is expected to have unique items.").format(name=name))

    value = [
        transform(schema["items"], f"{name}[{i}]", item, components) for i, item in enumerate(value)
    ]
    return value


def transform_boolean(
    schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> t.Any:
    _assert_type(name, value, bool, "boolean")
    return value


def transform_integer(
    schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> t.Any:
    _assert_type(name, value, int, "integer")
    _assert_min_max(schema, name, value)

    if (multiple_of := schema.get("multipleOf")) is not None:
        if value % multiple_of != 0:
            raise ValidationError(
                _("'{name}' is expected to be a multiple of {multiple_of}").format(
                    name=name, multiple_of=multiple_of
                )
            )

    return value


def transform_number(
    schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> t.Any:
    _assert_type(name, value, (float, int), "number")
    _assert_min_max(schema, name, value)
    return value


def transform_object(
    schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> t.Any:
    _assert_type(name, value, dict, "object")
    new_value = {}
    extra_value = {}
    properties = schema.get("properties", {})
    for pname, pvalue in value.items():
        if (pschema := properties.get(pname)) is not None:
            new_value[pname] = transform(pschema, f"{name}[{pname}]", pvalue, components)
        else:
            extra_value[pname] = pvalue
    additional_properties: t.Union[bool, t.Dict[str, t.Any]] = schema.get(
        "additionalProperties", {}
    )
    if len(extra_value) > 0:
        if additional_properties is False:
            raise ValidationError(
                _("'{name}' does not allow additional properties.").format(name=name)
            )
        elif isinstance(additional_properties, dict):
            extra_value = {
                pname: transform(additional_properties, f"{name}[{pname}]", pvalue, components)
                for pname, pvalue in extra_value.items()
            }
    new_value.update(extra_value)
    if (required := schema.get("required")) is not None:
        if missing_keys := set(required) - set(new_value.keys()):
            raise ValidationError(
                _("'{name}' is missing properties ({missing}).").format(
                    name=name, missing=", ".join(missing_keys)
                )
            )

    return new_value


def transform_string(
    schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> t.Any:
    schema_format = schema.get("format")
    if schema_format == "byte":
        _assert_type(name, value, bytes, "bytes")
        value = base64.b64encode(value).decode()
    elif schema_format == "binary":
        # This is not really useful for json serialization.
        # It is there for file transfer, e.g. in multipart.
        _assert_type(name, value, (bytes, io.BufferedReader, io.BytesIO), "binary")
    elif schema_format == "date":
        _assert_type(name, value, datetime.date, "date")
        value = value.strftime(ISO_DATE_FORMAT)
    elif schema_format == "date-time":
        _assert_type(name, value, datetime.datetime, "date-time")
        value = value.strftime(ISO_DATETIME_FORMAT)
    else:
        _assert_type(name, value, str, "string")
    if (enum := schema.get("enum")) is not None:
        if value not in enum:
            raise ValidationError(
                _("'{name}' is expected to be on of [{enums}].").format(
                    name=name, enums=", ".join(enum)
                )
            )
    return value


_TYPED_TRANSFORMS = {
    "array": transform_array,
    "boolean": transform_boolean,
    "integer": transform_integer,
    "number": transform_number,
    "object": transform_object,
    "string": transform_string,
}
