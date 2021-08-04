from inspect import isclass
from typing import Dict, Type, Union, cast

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from marshmallow import Schema

from .. import fields


def field2property(spec: APISpec, field: fields.Field):
    """Convert a marshmallow Field to OpenAPI dictionary

    We require an initialised APISpec object to use its
    converter function - in particular, this will depend
    on the OpenAPI version defined in `spec`.  We also rely
    on the spec having a `MarshmallowPlugin` attached.
    """
    plugin = get_marshmallow_plugin(spec)
    return plugin.converter.field2property(field)


def ensure_schema(
    spec: APISpec,
    schema: Union[
        fields.Field,
        Type[fields.Field],
        Schema,
        Type[Schema],
        Dict[str, Union[fields.Field, type]],
    ],
    name: str = "GeneratedFromDict",
) -> Union[dict, Schema]:
    """Create a Schema object, or OpenAPI dictionary, given a Field, Schema, or Dict.

    The output from this function should be suitable to include in a dictionary
    that is passed to APISpec.  Fields won't get processed by the Marshmallow
    plugin, and can't be converted to Schemas without adding a field name, so
    we convert them directly to the dictionary representation.

    Other Schemas are returned as Marshmallow Schema instances, which will be
    converted to references by the plugin.

    The first argument must be an initialised APISpec object, as the conversion
    of single fields to dictionaries is version-dependent.
    """
    if schema is None:
        return None
    if isinstance(schema, fields.Field):
        return field2property(spec, schema)
    elif isinstance(schema, dict):
        return Schema.from_dict(schema, name=name)()
    elif isinstance(schema, Schema):
        return schema
    if isclass(schema):
        schema = cast(Type, schema)
        if issubclass(schema, fields.Field):
            return field2property(spec, schema())
        elif issubclass(schema, Schema):
            return schema()
    raise TypeError(
        f"Invalid schema type {type(schema)}. Must be a Schema or Mapping/dict"
    )


def get_marshmallow_plugin(spec):
    """Extract the marshmallow plugin object from an APISpec"""
    for p in spec.plugins:
        if isinstance(p, MarshmallowPlugin):
            return p
    raise AttributeError("The APISpec does not seem to have a Marshmallow plugin.")
