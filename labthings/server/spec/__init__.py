from ..view import View
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from ...core.utilities import get_docstring, get_summary, rupdate

from ..fields import Field
from marshmallow import Schema as BaseSchema

from .paths import rule_to_path, rule_to_params

from werkzeug.routing import Rule
from collections import Mapping
from http import HTTPStatus


def update_spec(obj, spec):
    obj.__apispec__ = obj.__dict__.get("__apispec__", {})
    rupdate(obj.__apispec__, spec)
    return obj.__apispec__


def get_spec(obj):
    obj.__apispec__ = obj.__dict__.get("__apispec__", {})
    return obj.__apispec__


def rule2path(rule: Rule, view: View, spec: APISpec):
    params = {
        "path": rule_to_path(rule),
        "operations": view2operations(view, spec),
        "description": get_docstring(view),
        "summary": get_summary(view),
    }

    # Add URL arguments
    if rule.arguments:
        for op in params.get("operations").keys():
            params["operations"][op].update({"parameters": rule_to_params(rule)})

    # Add extra parameters
    if hasattr(view, "__apispec__"):
        # Recursively update params
        rupdate(params, view.__apispec__)

    return params


def view2operations(view: View, spec: APISpec):
    # Operations inherit tags from parent
    inherited_tags = []
    if hasattr(view, "__apispec__"):
        inherited_tags = getattr(view, "__apispec__").get("tags", [])

    # Build dictionary of operations (HTTP methods)
    ops = {}
    for method in View.methods:
        if hasattr(view, method):
            ops[method] = {}

            rupdate(
                ops[method],
                {
                    "description": get_docstring(getattr(view, method)),
                    "summary": get_summary(getattr(view, method)),
                    "tags": inherited_tags,
                },
            )

            rupdate(ops[method], method2operation(getattr(view, method), spec))

    return ops


def method2operation(method: callable, spec: APISpec):
    if hasattr(method, "__apispec__"):
        apispec = getattr(method, "__apispec__")
    else:
        apispec = {}

    op = {}
    if "_params" in apispec:
        rupdate(
            op,
            {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": convert_schema(apispec.get("_params"), spec)
                        }
                    }
                }
            },
        )

    if "_schema" in apispec:
        for code, schema in apispec.get("_schema", {}).items():
            rupdate(
                op,
                {
                    "responses": {
                        code: {
                            "description": HTTPStatus(code).phrase,
                            "content": {
                                "application/json": {
                                    "schema": convert_schema(schema, spec)
                                }
                            },
                        }
                    }
                },
            )
    else:
        # If no explicit responses are known, populate with defaults
        rupdate(
            op,
            {
                "responses": {
                    200: {"description": get_summary(method) or HTTPStatus(200).phrase}
                }
            },
        )

    # Bung in any extra swagger fields supplied
    for key, val in apispec.items():
        if not key in ["_params", "_schema"]:
            rupdate(op, {key: val})

    return op


def convert_schema(schema, spec: APISpec):
    """
    Ensure that a given schema is either a real Marshmallow schema, 
    or is a dictionary describing the schema inline.

    Marshmallow schemas are left as they are so that the APISpec module
    can add them to the "schemas" list in our APISpec documentation.
    """
    if isinstance(schema, BaseSchema):
        return schema
    elif isinstance(schema, Mapping):
        return map2properties(schema, spec)
    elif isinstance(schema, Field):
        return field2property(schema, spec)
    else:
        raise TypeError(
            "Unsupported schema type. Ensure schema is a Schema class, or dictionary of Field objects"
        )


def map2properties(schema, spec: APISpec):
    """
    Convert any dictionary-like map of Marshmallow fields into a dictionary describing it's JSON schema
    """
    marshmallow_plugin = next(
        plugin for plugin in spec.plugins if isinstance(plugin, MarshmallowPlugin)
    )
    converter = marshmallow_plugin.converter

    d = {}
    for k, v in schema.items():
        if isinstance(v, Field):
            d[k] = converter.field2property(v)
        elif isinstance(v, Mapping):
            d[k] = map2properties(v, spec)
        else:
            d[k] = v

    return {"type": "object", "properties": d}


def field2property(field, spec: APISpec):
    """
    Convert a single Marshmallow field into a JSON schema of that field
    """
    marshmallow_plugin = next(
        plugin for plugin in spec.plugins if isinstance(plugin, MarshmallowPlugin)
    )
    converter = marshmallow_plugin.converter

    return converter.field2property(field)


def schema2json(schema, spec: APISpec):
    """
    Convert any Marshmallow schema, field, or dictionary of fields stright to a JSON schema
    This should not be used when generating APISpec documentation, otherwise schemas wont
    be listed in the "schemas" list. This is used, for example, in the Thing Description.
    """
    if not isinstance(schema, BaseSchema):
        schema = convert_schema(schema, spec)

    if isinstance(schema, BaseSchema):
        marshmallow_plugin = next(
            plugin for plugin in spec.plugins if isinstance(plugin, MarshmallowPlugin)
        )
        converter = marshmallow_plugin.converter

        schema = converter.schema2jsonschema(schema)

    return schema
