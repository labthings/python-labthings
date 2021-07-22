from inspect import isclass
from typing import Dict, Union

from apispec.ext.marshmallow import MarshmallowPlugin
from apispec.ext.marshmallow.field_converter import FieldConverterMixin
from marshmallow import Schema

from .. import fields


def field2property(field):
    """Convert a marshmallow Field to OpenAPI dictionary"""
    converter = FieldConverterMixin()
    converter.init_attribute_functions()
    return converter.field2property(field)


def ensure_schema(
    schema: Union[fields.Field, Schema, Dict[str, Union[fields.Field, type]]],
    name: str = "GeneratedFromDict",
) -> Union[dict, Schema]:
    """Create a Schema object, or OpenAPI dictionary, given a Field, Schema, or Dict.

    The output from this function should be suitable to include in a dictionary
    that is passed to APISpec.  Fields won't get processed by the Marshmallow
    plugin, and can't be converted to Schemas without adding a field name, so
    we convert them directly to the dictionary representation.

    Other Schemas are returned as Marshmallow Schema instances, which will be
    converted to references by the plugin.
    """
    if schema is None:
        return None
    if isinstance(schema, fields.Field):
        return field2property(schema)
    if isclass(schema) and issubclass(schema, fields.Field):
        return field2property(schema())
    elif isinstance(schema, dict):
        return Schema.from_dict(schema, name=name)()
    elif isinstance(schema, Schema):
        return schema
    elif isclass(schema) and issubclass(schema, Schema):
        return schema()
    else:
        raise TypeError(
            f"Invalid schema type {type(schema)}. Must be a Schema or Mapping/dict"
        )


def get_marshmallow_plugin(spec):
    """Extract the marshmallow plugin object from an APISpec"""
    for p in spec.plugins:
        if isinstance(p, MarshmallowPlugin):
            return p
    raise AttributeError("The APISpec does not seem to have a Marshmallow plugin.")
