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


def encode_param(value: t.Any) -> t.Any:
    if isinstance(value, list):
        return [encode_param(item) for item in value]
    if isinstance(value, datetime.datetime):
        return value.strftime(ISO_DATETIME_FORMAT)
    elif isinstance(value, datetime.date):
        return value.strftime(ISO_DATE_FORMAT)
    else:
        return value


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


def validate(schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]) -> None:
    if (schema_ref := schema.get("$ref")) is not None:
        # From json-schema:
        # "All other properties in a "$ref" object MUST be ignored."
        _validate_ref(schema_ref, name, value, components)
        return

    if value is None:
        # This seems to be the openapi 3.0.3 way.
        # in 3.1.* they use `"type": ["string", "null"]` instead.
        if schema.get("nullable", False):
            return

    if (schema_type := schema.get("type")) is not None:
        if isinstance(schema_type, list):
            if len(schema_type) == 0:
                raise SchemaError(_("{name} specified an empty type array").format(name=name))
            errors = []
            for stype in schema_type:
                try:
                    _validate_type(stype, schema, name, value, components)
                    break
                except ValidationError as e:
                    errors.append(f"{stype}: {e}")
            else:
                raise ValidationError(
                    _("{name} did not match any of the types: {errors}").format(
                        name=name, errors="\n".join(errors)
                    )
                )

        else:
            _validate_type(schema_type, schema, name, value, components)

    # allOf etc allow for composition, but the spec isn't particularly clear about that.
    if (all_of := schema.get("allOf")) is not None:
        if isinstance(value, dict):
            value = value.copy()
            for sub_schema in all_of:
                validate(sub_schema, name, value, components)
        else:
            # This may not even be a valid case according to the specification.
            # But it is used by drf-spectacular to reference enum-strings.
            for sub_schema in all_of:
                validate(sub_schema, name, value, components)

    if (any_of := schema.get("anyOf")) is not None:
        for sub_schema in any_of:
            with suppress(ValidationError):
                validate(sub_schema, name, value, components)
                break
        else:
            raise ValidationError(
                _("'{name}' does not match any of the provide schemata.").format(name=name)
            )


def _validate_type(
    schema_type: str, schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> None:
    if (typed_validator := _TYPED_VALIDATORS.get(schema_type)) is not None:
        typed_validator(schema, name, value, components)
    else:
        raise NotImplementedError(
            _("Type `{schema_type}` is not implemented yet.").format(schema_type=schema_type)
        )


def _validate_ref(schema_ref: str, name: str, value: t.Any, components: t.Dict[str, t.Any]) -> None:
    if not schema_ref.startswith("#/components/schemas/"):
        raise SchemaError(_("'{name}' contains an invalid reference.").format(name=name))
    schema_name = schema_ref[21:]
    validate(components[schema_name], name, value, components)


def _validate_array(schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]) -> None:
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

    for i, item in enumerate(value):
        validate(schema["items"], f"{name}[{i}]", item, components)


def _validate_boolean(
    schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> None:
    _assert_type(name, value, bool, "boolean")


def _validate_integer(
    schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> None:
    _assert_type(name, value, int, "integer")
    _assert_min_max(schema, name, value)

    if (multiple_of := schema.get("multipleOf")) is not None:
        if value % multiple_of != 0:
            raise ValidationError(
                _("'{name}' is expected to be a multiple of {multiple_of}").format(
                    name=name, multiple_of=multiple_of
                )
            )


def _validate_null(schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]) -> None:
    if value is not None:
        raise ValidationError(_("'{name}' is expected to be a null").format(name=name))


def _validate_number(
    schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> None:
    _assert_type(name, value, (float, int), "number")
    _assert_min_max(schema, name, value)


def _validate_object(
    schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> None:
    _assert_type(name, value, dict, "object")
    extra_values = {}
    properties = schema.get("properties", {})
    for pname, pvalue in value.items():
        if (pschema := properties.get(pname)) is not None:
            validate(pschema, f"{name}[{pname}]", pvalue, components)
        else:
            extra_values[pname] = pvalue
    additional_properties: t.Union[bool, t.Dict[str, t.Any]] = schema.get(
        "additionalProperties", {}
    )
    if len(extra_values) > 0:
        if additional_properties is False:
            raise ValidationError(
                _("'{name}' does not allow additional properties.").format(name=name)
            )
        elif isinstance(additional_properties, dict):
            for pname, pvalue in extra_values.items():
                validate(additional_properties, f"{name}[{pname}]", pvalue, components)
    if (required := schema.get("required")) is not None:
        if missing_keys := set(required) - set(value.keys()):
            raise ValidationError(
                _("'{name}' is missing properties ({missing}).").format(
                    name=name, missing=", ".join(missing_keys)
                )
            )


def _validate_string(
    schema: t.Any, name: str, value: t.Any, components: t.Dict[str, t.Any]
) -> None:
    schema_format = schema.get("format")
    if schema_format == "byte":
        _assert_type(name, value, bytes, "bytes")
    elif schema_format == "binary":
        # This is not really useful for json serialization.
        # It is there for file transfer, e.g. in multipart.
        _assert_type(name, value, (bytes, io.BufferedReader, io.BytesIO), "binary")
    elif schema_format == "date":
        _assert_type(name, value, datetime.date, "date")
    elif schema_format == "date-time":
        _assert_type(name, value, datetime.datetime, "date-time")
    else:
        _assert_type(name, value, str, "string")
    if (enum := schema.get("enum")) is not None:
        if value not in enum:
            raise ValidationError(
                _("'{name}' is expected to be one of [{enums}].").format(
                    name=name, enums=", ".join(enum)
                )
            )


_TYPED_VALIDATORS = {
    "array": _validate_array,
    "boolean": _validate_boolean,
    "integer": _validate_integer,
    "null": _validate_null,
    "number": _validate_number,
    "object": _validate_object,
    "string": _validate_string,
}
