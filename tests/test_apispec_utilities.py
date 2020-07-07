from labthings.apispec import utilities
from marshmallow import fields
import pytest


def test_convert_schema_none(spec):
    assert not utilities.convert_to_schema_or_json(None, spec)


def test_convert_schema_schema(spec):
    from marshmallow import Schema

    schema = Schema()
    schema.integer = fields.Int()
    assert utilities.convert_to_schema_or_json(schema, spec) is schema


def test_convert_schema_map(spec):
    schema = {"integer": fields.Int()}
    assert utilities.convert_to_schema_or_json(schema, spec) == {
        "type": "object",
        "properties": {"integer": {"type": "integer", "format": "int32"}},
    }


def test_convert_schema_field(spec):
    schema = fields.Int()
    assert utilities.convert_to_schema_or_json(schema, spec) == {
        "type": "integer",
        "format": "int32",
    }


def test_convert_schema_invalid(spec):
    schema = object()

    with pytest.raises(TypeError):
        utilities.convert_to_schema_or_json(schema, spec)


def test_map_to_schema_nested(spec):
    schema = {"submap": {"integer": fields.Int()}}

    assert utilities.map_to_properties(schema, spec) == {
        "type": "object",
        "properties": {
            "submap": {
                "type": "object",
                "properties": {"integer": {"type": "integer", "format": "int32"}},
            }
        },
    }


def test_map_to_schema_json(spec):
    schema = {"key": "value"}

    assert utilities.map_to_properties(schema, spec) == {
        "type": "object",
        "properties": {"key": "value"},
    }


def test_schema_to_json(spec):
    from marshmallow import Schema

    UserSchema = Schema.from_dict({"name": fields.Str(), "email": fields.Email()})

    assert utilities.schema_to_json(UserSchema(), spec) == {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
        },
    }


def test_schema_to_json_json_in(spec):
    from marshmallow import Schema

    input_dict = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
        },
    }

    assert utilities.schema_to_json(input_dict, spec) == input_dict


def test_recursive_expand_refs(spec):
    from marshmallow import Schema

    UserSchema = Schema.from_dict({"name": fields.Str(), "email": fields.Email()})
    TestParentSchema = Schema.from_dict({"author": fields.Nested(UserSchema)})

    assert utilities.schema_to_json(TestParentSchema(), spec) == {
        "type": "object",
        "properties": {
            "author": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "name": {"type": "string"},
                },
            }
        },
    }


def test_recursive_expand_refs_schema_in(spec):
    from marshmallow import Schema

    UserSchema = Schema.from_dict({"name": fields.Str(), "email": fields.Email()})

    user_schema_instance = UserSchema()
    assert (
        utilities.recursive_expand_refs(user_schema_instance, spec)
        == user_schema_instance
    )


### TODO: Test expand_refs


def test_expand_refs_no_refs(spec):
    input_dict = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
        },
    }

    assert utilities.expand_refs(input_dict, spec) == input_dict


def test_expand_refs_missing_schema(spec):
    input_dict = {"$ref": "MissingRef"}

    assert utilities.expand_refs(input_dict, spec) == input_dict
