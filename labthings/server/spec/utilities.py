from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from ...core.utilities import rupdate

from ..fields import Field
from marshmallow import Schema as BaseSchema

from collections import Mapping


def update_spec(obj, spec):
    obj.__apispec__ = obj.__dict__.get("__apispec__", {})
    rupdate(obj.__apispec__, spec)
    return obj.__apispec__ or {}


def get_spec(obj):
    obj.__apispec__ = obj.__dict__.get("__apispec__", {})
    return obj.__apispec__ or {}


def convert_schema(schema, spec: APISpec):
    """
    Ensure that a given schema is either a real Marshmallow schema,
    or is a dictionary describing the schema inline.

    Marshmallow schemas are left as they are so that the APISpec module
    can add them to the "schemas" list in our APISpec documentation.
    """
    # Don't process Nones
    if not schema:
        return schema

    # Expand/convert actual schema data
    if isinstance(schema, BaseSchema):
        return schema
    elif isinstance(schema, Mapping):
        return map_to_properties(schema, spec)
    elif isinstance(schema, Field):
        return field_to_property(schema, spec)
    else:
        raise TypeError(
            f"Unsupported schema type {schema}. "
            "Ensure schema is a Schema class, or dictionary of Field objects"
        )


def map_to_properties(schema, spec: APISpec):
    """
    Recursively convert any dictionary-like map of Marshmallow fields
    into a dictionary describing it's JSON schema
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
            d[k] = map_to_properties(v, spec)
        else:
            d[k] = v

    return {"type": "object", "properties": d}


def field_to_property(field, spec: APISpec):
    """
    Convert a single Marshmallow field into a JSON schema of that field
    """
    marshmallow_plugin = next(
        plugin for plugin in spec.plugins if isinstance(plugin, MarshmallowPlugin)
    )
    converter = marshmallow_plugin.converter

    return converter.field2property(field)


def schema_to_json(schema, spec: APISpec):
    """
    Convert any Marshmallow schema stright to a fully expanded JSON schema.
    This should not be used when generating APISpec documentation,
    otherwise schemas wont be listed in the "schemas" list.
    This is used, for example, in the Thing Description.
    """

    if isinstance(schema, BaseSchema):
        marshmallow_plugin = next(
            plugin for plugin in spec.plugins if isinstance(plugin, MarshmallowPlugin)
        )
        converter = marshmallow_plugin.converter

        schema = converter.schema2jsonschema(schema)

    schema = recursive_expand_refs(schema, spec)

    return schema


def recursive_expand_refs(schema_dict, spec: APISpec):
    """
    Traverse `schema_dict` expanding out all schema $ref values where possible.

    Used when generating Thing Descriptions, so each attribute contains full schemas.
    """
    if isinstance(schema_dict, Mapping):
        if "$ref" in schema_dict:
            schema_dict = expand_refs(schema_dict, spec)

        for k, v in schema_dict.items():
            if isinstance(v, Mapping):
                schema_dict[k] = recursive_expand_refs(v, spec)

    return schema_dict


def expand_refs(schema_dict, spec: APISpec):
    """
    Expand out all schema $ref values where possible.

    Uses the $ref value to look up a particular schema in spec schemas
    """
    if "$ref" not in schema_dict:
        return schema_dict

    name = schema_dict.get("$ref").split("/")[-1]

    # Get the list of all schemas registered with APISpec
    spec_schemas = spec.to_dict().get("components", {}).get("schemas", {})

    if name in spec_schemas:
        schema_dict.update(spec_schemas.get(name))
        del schema_dict["$ref"]

    return schema_dict
