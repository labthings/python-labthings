import pytest

from labthings import fields, schema
from labthings.actions.thread import ActionThread
from labthings.extensions import BaseExtension


def test_field_schema(app_ctx):
    test_schema = schema.FieldSchema(fields.String())

    assert test_schema.serialize(5) == "5"
    assert test_schema.dump(5) == "5"
    assert test_schema.deserialize("string") == "string"


def test_extension_schema(app_ctx):
    test_schema = schema.ExtensionSchema()
    test_extension = BaseExtension("org.labthings.tests.extension")

    with app_ctx.test_request_context():
        d = test_schema.dump(test_extension)
        assert isinstance(d, dict)
        assert "pythonName" in d
        assert d.get("pythonName") == "org.labthings.tests.extension"
        assert "links" in d
        assert isinstance(d.get("links"), dict)


def test_build_action_schema():
    input_schema = schema.Schema()
    output_schema = schema.Schema()
    action_schema = schema.build_action_schema(input_schema, output_schema)

    assert issubclass(action_schema, schema.ActionSchema)
    declared_fields = action_schema._declared_fields
    assert "input" in declared_fields
    assert "output" in declared_fields


def test_build_action_schema_fields():
    input_schema = fields.Field()
    output_schema = fields.Field()
    action_schema = schema.build_action_schema(input_schema, output_schema)

    assert issubclass(action_schema, schema.ActionSchema)
    declared_fields = action_schema._declared_fields
    assert "input" in declared_fields
    assert "output" in declared_fields


def test_build_action_schema_nones():
    input_schema = None
    output_schema = None
    action_schema = schema.build_action_schema(input_schema, output_schema)

    assert issubclass(action_schema, schema.ActionSchema)
    declared_fields = action_schema._declared_fields
    assert "input" in declared_fields
    assert "output" in declared_fields


def test_build_action_schema_typeerror():
    input_schema = object()
    output_schema = object()
    with pytest.raises(TypeError):
        action_schema = schema.build_action_schema(input_schema, output_schema)


def test_nest_if_needed():
    nested_schema = schema.nest_if_needed(schema.ActionSchema())
    assert isinstance(nested_schema, fields.Field)
    nested_dict = schema.nest_if_needed({"name": fields.Integer()})
    assert isinstance(nested_schema, fields.Field)
    nested_field = schema.nest_if_needed(fields.Boolean())
    assert isinstance(nested_schema, fields.Field)
