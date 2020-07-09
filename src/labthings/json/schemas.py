from marshmallow import Schema, fields
from .marshmallow_jsonschema import JSONSchema
from collections.abc import Mapping


def field_to_property(field):
    return JSONSchema()._get_schema_for_field(Schema(), field)


def map_to_schema(schema_dict: dict):
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
