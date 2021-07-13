from apispec.ext.marshmallow import MarshmallowPlugin
from apispec.ext.marshmallow.field_converter import FieldConverterMixin
from apispec.ext.marshmallow.schema_resolver import SchemaResolver
from marshmallow import Schema
from typing import Dict, Union
from .. import fields

def field2property(field):
    """Convert a marshmallow Field to OpenAPI dictionary"""
    converter = FieldConverterMixin()
    converter.init_attribute_functions()
    return converter.field2pattern(field)

def ensure_schema(
    schema: Union[fields.Field, Schema, Dict[str, Union[fields.Field, type]]], 
    name: str = "GeneratedFromDict"
) -> Union[dict, Schema]:
    """Create a Schema object, or OpenAPI dictionary, given a Field, Schema, or Dict.
    """
    if schema is None:
        return None
    if isinstance(schema, fields.Field):
        return field2property(schema)
    elif isinstance(schema, dict):
        return Schema.from_dict(schema, name=name)()
    elif isinstance(schema, Schema):
        return schema
    else:
        raise TypeError(
            f"Invalid schema type {type(schema)}. Must be a Schema or Mapping/dict"
        )

def get_marshamallow_plugin(spec):
    """Extract the marshmallow plugin object from an APISpec"""
    for p in spec.plugins:
        if isinstance(p, MarshmallowPlugin):
            return p
    raise AttributeError("The APISpec does not seem to have a Marshmallow plugin.")