import werkzeug.routing
import re
from marshmallow import Schema, fields
from collections.abc import Mapping
from .marshmallow_jsonschema import JSONSchema


PATH_RE = re.compile(r"<(?:[^:<>]+:)?([^<>]+)>")
# Conversion map of werkzeug rule converters to Javascript schema types
CONVERTER_MAPPING = {
    werkzeug.routing.UnicodeConverter: ("string", None),
    werkzeug.routing.IntegerConverter: ("integer", "int32"),
    werkzeug.routing.FloatConverter: ("number", "float"),
}

DEFAULT_TYPE = ("string", None)


def rule_to_path(rule):
    """Convert a Flask rule into an JSON schema formatted URL path

    :param rule: Flask rule object
    :returns: URL path
    :rtype: str

    """
    return PATH_RE.sub(r"{\1}", rule.rule)


def rule_to_params(rule, overrides=None):
    """Convert a Flask rule into JSON schema URL parameters description

    :param rule: Flask rule object
    :param overrides: Optional dictionary to override params with (Default value = None)
    :type overrides: dict
    :returns: Dictionary of URL parameters
    :rtype: dict

    """
    overrides = overrides or {}
    result = [
        argument_to_param(argument, rule, overrides.get(argument, {}))
        for argument in rule.arguments
    ]
    for key in overrides.keys():
        if overrides[key].get("in") in ("header", "query"):
            overrides[key]["name"] = overrides[key].get("name", key)
            result.append(overrides[key])
    return result


def argument_to_param(argument, rule, override=None):
    """Convert a Flask rule into APISpec URL parameters description

    :param argument: URL argument
    :type argument: str
    :param rule: Flask rule object
    :param override: Optional dictionary to override params with (Default value = None)
    :type override: dict
    :returns: Dictionary of URL parameter description
    :rtype: dict

    """
    param = {"in": "path", "name": argument, "required": True}
    type_, format_ = CONVERTER_MAPPING.get(
        # skipcq: PYL-W0212
        type(rule._converters[argument]),
        DEFAULT_TYPE,
    )
    param["schema"] = {}
    param["schema"]["type"] = type_
    if format_ is not None:
        param["format"] = format_
    if rule.defaults and argument in rule.defaults:
        param["default"] = rule.defaults[argument]
    param.update(override or {})
    return param


def field_to_property(field):
    """

    :param field: 

    """
    return JSONSchema()._get_schema_for_field(Schema(), field)


def map_to_schema(schema_dict: dict):
    """

    :param schema_dict: dict: 

    """
    d = {}

    for k, v in schema_dict.items():
        if isinstance(v, fields.Field):
            d[k] = v
        elif isinstance(v, Mapping):
            d[k] = fields.Nested(Schema.from_dict(v))
        else:
            raise TypeError(f"Invalid field type {type(v)} for schema")

    return Schema.from_dict(d)


def schema_to_json(schema):
    """

    :param schema: 

    """
    if schema is None:
        return None
    if isinstance(schema, fields.Field):
        return field_to_property(schema)
    elif isinstance(schema, Mapping):
        return JSONSchema().dump(map_to_schema(schema)())
    elif isinstance(schema, Schema):
        return JSONSchema().dump(schema)
    else:
        raise TypeError(
            f"Invalid schema type {type(schema)}. Must be a Schema or Mapping/dict"
        )
