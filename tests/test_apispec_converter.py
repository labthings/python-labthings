from labthings import fields
from labthings.apispec.converter import ExtendedOpenAPIConverter


class TestField(fields.Field):
    def _jsonschema_type_mapping(self):
        """ """
        return {"type": "string"}


def test_jsonschema_type_mapping(spec):
    converter = ExtendedOpenAPIConverter("3.0.2", lambda _: None, spec)

    assert converter.jsonschema_type_mapping(TestField()) == {"type": "string"}


def test_jsonschema_type_mapping_missing(spec):
    converter = ExtendedOpenAPIConverter("3.0.2", lambda _: None, spec)

    assert converter.jsonschema_type_mapping(fields.Field()) == {}
