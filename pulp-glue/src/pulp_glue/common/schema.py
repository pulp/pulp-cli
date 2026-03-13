import datetime
import io
import json
import typing as t
from contextlib import suppress

from pulp_glue.common import oas
from pulp_glue.common.exceptions import SchemaError, ValidationError
from pulp_glue.common.i18n import get_translation

translation = get_translation(__package__)
_ = translation.gettext

ISO_DATE_FORMAT = "%Y-%m-%d"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


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
    elif isinstance(value, bool):
        return "true" if value else "false"
    else:
        return value


def _assert_type(
    name: str,
    value: t.Any,
    types: t.Type[object] | tuple[t.Type[object], ...],
    type_name: str,
) -> None:
    if not isinstance(value, types):
        raise ValidationError(
            _("'{name}' is expected to be a {type_name}.").format(name=name, type_name=type_name)
        )


def _assert_min_max(schema: oas.TypeSchema, name: str, value: int | float) -> None:
    if schema.minimum is not None:
        if schema.exclusive_minimum:
            if schema.minimum >= value:
                raise ValidationError(
                    _("'{name}' is expected to be larger than {minimum}").format(
                        name=name, minimum=schema.minimum
                    )
                )
        else:
            if schema.minimum > value:
                raise ValidationError(
                    _("'{name}' is expected to not be smaller than {minimum}").format(
                        name=name, minimum=schema.minimum
                    )
                )
    if schema.maximum is not None:
        if schema.exclusive_maximum:
            if schema.maximum <= value:
                raise ValidationError(
                    _("'{name}' is expected to be smaller than {maximum}").format(
                        name=name, maximum=schema.maximum
                    )
                )
        else:
            if schema.maximum < value:
                raise ValidationError(
                    _("'{name}' is expected to not be larger than {maximum}").format(
                        name=name, maximum=schema.maximum
                    )
                )


def validate(
    schema: oas.Schema, name: str, value: t.Any, components: dict[str, oas.Schema]
) -> None:
    if isinstance(schema, bool):
        # 'true' and 'false' can be used as allow/deny anything quantors.
        if schema is False:
            raise ValidationError(_("'{name}' does not allow to be validated.").format(name=name))
        return
    if isinstance(schema, oas.Reference):
        # From json-schema:
        # "All other properties in a "$ref" object MUST be ignored."
        _validate_ref(schema.ref, name, value, components)
        return

    if value is None:
        # This seems to be the openapi 3.0.3 way.
        # in 3.1.* they use `"type": ["string", "null"]` instead.
        if schema.nullable:
            return

    if isinstance(schema, oas.TypeSchema):
        if isinstance(schema.type_, list):
            if len(schema.type_) == 0:
                raise SchemaError(_("{name} specified an empty type array").format(name=name))
            errors = []
            for stype in schema.type_:
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
            _validate_type(schema.type_, schema, name, value, components)

    # allOf etc allow for composition, but the spec isn't particularly clear about that.
    elif isinstance(schema, oas.AllOfSchema):
        for sub_schema in schema.all_of:
            validate(sub_schema, name, value, components)

    elif isinstance(schema, oas.AnyOfSchema):
        for sub_schema in schema.any_of:
            with suppress(ValidationError):
                validate(sub_schema, name, value, components)
                break
        else:
            raise ValidationError(
                _("'{name}' does not match any of the provided schemata.").format(name=name)
            )

    elif isinstance(schema, oas.OneOfSchema):
        found = 0
        for sub_schema in schema.one_of:
            with suppress(ValidationError):
                validate(sub_schema, name, value, components)
                found += 1
            if found > 1:
                raise ValidationError(
                    _("'{name} matches more than one of the provided schemata.").format(name=name)
                )
        if not found:
            raise ValidationError(
                _("'{name}' does not match any of the provided schemata.").format(name=name)
            )


def _validate_type(
    schema_type: str, schema: oas.TypeSchema, name: str, value: t.Any, components: dict[str, t.Any]
) -> None:
    if (typed_validator := _TYPED_VALIDATORS.get(schema_type)) is None:
        raise NotImplementedError(
            _("Type `{schema_type}` is not implemented yet.").format(schema_type=schema_type)
        )
    typed_validator(schema, name, value, components)


def _validate_ref(schema_ref: str, name: str, value: t.Any, components: dict[str, t.Any]) -> None:
    if not schema_ref.startswith("#/components/schemas/"):
        raise SchemaError(_("'{name}' contains an invalid reference.").format(name=name))
    schema_name = schema_ref[21:]
    try:
        validate(components[schema_name], name, value, components)
    except KeyError:
        raise SchemaError(_("Could not resolve reference '{name}'."))


def _validate_array(
    schema: oas.TypeSchema, name: str, value: t.Any, components: dict[str, t.Any]
) -> None:
    _assert_type(name, value, list, "array")
    if schema.min_items is not None:
        if len(value) < schema.min_items:
            raise ValidationError(
                _("'{name}' is expected to have at least {min_items} items.").format(
                    name=name, min_items=schema.min_items
                )
            )
    if schema.max_items is not None:
        if len(value) > schema.max_items:
            raise ValidationError(
                _("'{name}' is expected to have at most {max_items} items.").format(
                    name=name, max_items=schema.max_items
                )
            )
    if schema.unique_items:
        if len(set(value)) != len(value):
            raise ValidationError(_("'{name}' is expected to have unique items.").format(name=name))

    if schema.items is not None:
        for i, item in enumerate(value):
            validate(schema.items, f"{name}[{i}]", item, components)


def _validate_boolean(
    schema: oas.TypeSchema, name: str, value: t.Any, components: dict[str, t.Any]
) -> None:
    _assert_type(name, value, bool, "boolean")


def _validate_integer(
    schema: oas.TypeSchema, name: str, value: t.Any, components: dict[str, t.Any]
) -> None:
    _assert_type(name, value, int, "integer")
    _assert_min_max(schema, name, value)

    if schema.multiple_of is not None:
        if value % schema.multiple_of != 0:
            raise ValidationError(
                _("'{name}' is expected to be a multiple of {multiple_of}").format(
                    name=name, multiple_of=schema.multiple_of
                )
            )


def _validate_null(
    schema: oas.TypeSchema, name: str, value: t.Any, components: dict[str, t.Any]
) -> None:
    if value is not None:
        raise ValidationError(_("'{name}' is expected to be a null").format(name=name))


def _validate_number(
    schema: oas.TypeSchema, name: str, value: t.Any, components: dict[str, t.Any]
) -> None:
    _assert_type(name, value, (float, int), "number")
    _assert_min_max(schema, name, value)


def _validate_object(
    schema: oas.TypeSchema, name: str, value: t.Any, components: dict[str, t.Any]
) -> None:
    _assert_type(name, value, dict, "object")
    extra_values = {}
    if schema.properties is not None:
        for pname, pvalue in value.items():
            if (pschema := schema.properties.get(pname)) is not None:
                validate(pschema, f"{name}[{pname}]", pvalue, components)
            else:
                extra_values[pname] = pvalue
    else:
        extra_values = value
    if len(extra_values) > 0:
        if schema.additional_properties is False:
            raise ValidationError(
                _("'{name}' does not allow additional properties.").format(name=name)
            )
        for pname, pvalue in extra_values.items():
            validate(schema.additional_properties, f"{name}[{pname}]", pvalue, components)
    if schema.required is not None:
        if missing_keys := set(schema.required) - set(value.keys()):
            raise ValidationError(
                _("'{name}' is missing properties ({missing}).").format(
                    name=name, missing=", ".join(missing_keys)
                )
            )


def _validate_string(
    schema: oas.TypeSchema, name: str, value: t.Any, components: dict[str, t.Any]
) -> None:
    schema_format = schema.format_
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
    if schema.enum is not None:
        if value not in schema.enum:
            raise ValidationError(
                _("'{name}' is expected to be one of [{enums}].").format(
                    name=name, enums=", ".join(schema.enum)
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
