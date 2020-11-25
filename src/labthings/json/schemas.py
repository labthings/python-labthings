import re
from typing import Any, Dict, List, Optional, Union

import werkzeug.routing
from marshmallow import Schema, fields

from .marshmallow_jsonschema import JSONSchema

PATH_RE = re.compile(r"<(?:[^:<>]+:)?([^<>]+)>")
# Conversion map of werkzeug rule converters to Javascript schema types
CONVERTER_MAPPING = {
    werkzeug.routing.UnicodeConverter: ("string", None),
    werkzeug.routing.IntegerConverter: ("integer", "int32"),
    werkzeug.routing.FloatConverter: ("number", "float"),
}

DEFAULT_TYPE = ("string", None)


def rule_to_path(rule) -> str:
    """Convert a Flask rule into an JSON schema formatted URL path

    :param rule: Flask rule object
    :returns: URL path
    :rtype: str

    """
    return PATH_RE.sub(r"{\1}", rule.rule)


def rule_to_params(rule: werkzeug.routing.Rule, overrides=None) -> List[Dict[str, Any]]:
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


def argument_to_param(
    argument: str,
    rule: werkzeug.routing.Rule,
    override: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Convert a Flask rule into APISpec URL parameters description

    :param argument: URL argument
    :type argument: str
    :param rule: Flask rule object
    :param override: Optional dictionary to override params with (Default value = None)
    :type override: dict
    :returns: Dictionary of URL parameter description
    :rtype: dict

    """
    param: Dict[str, Any] = {"in": "path", "name": argument, "required": True}
    type_, format_ = CONVERTER_MAPPING.get(
        # pylint: disable=protected-access
        type(rule._converters[argument]),  # type: ignore
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


def field_to_property(field: fields.Field):
    """

    :param field:

    """
    # pylint: disable=protected-access
    return JSONSchema()._get_schema_for_field(Schema(), field)


def schema_to_json(
    schema: Union[fields.Field, Schema, Dict[str, Union[fields.Field, type]]]
) -> dict:
    """

    :param schema:

    """
    if schema is None:
        return None
    if isinstance(schema, fields.Field):
        return field_to_property(schema)
    elif isinstance(schema, dict):
        return JSONSchema().dump(Schema.from_dict(schema)())
    elif isinstance(schema, Schema):
        return JSONSchema().dump(schema)
    else:
        raise TypeError(
            f"Invalid schema type {type(schema)}. Must be a Schema or Mapping/dict"
        )
