from labthings import fields
from labthings.marshalling import marshalling as ms
from labthings.schema import Schema


def test_schema_to_converter_schema():
    class TestSchema(Schema):
        foo = fields.String()

    test_schema = TestSchema()
    converter = ms.schema_to_converter(test_schema)
    assert converter == test_schema.dump
    assert converter({"foo": 5}) == {"foo": "5"}


def test_schema_to_converter_map():
    test_schema = {"foo": fields.String()}
    converter = ms.schema_to_converter(test_schema)
    assert converter({"foo": 5}) == {"foo": "5"}


def test_schema_to_converter_field():
    field = fields.String()
    converter = ms.schema_to_converter(field)
    assert converter(5) == "5"


def test_schema_to_converter_none():
    assert ms.schema_to_converter(object()) is None
