from labthings.apispec.converter import ExtendedOpenAPIConverter

from labthings import fields


class ExampleField(fields.Field):
    def _jsonschema_type_mapping(self):
        """ """
        return {"type": "string"}


def test_jsonschema_type_mapping(spec):
    converter = ExtendedOpenAPIConverter("3.0.2", lambda _: None, spec)

    assert converter.jsonschema_type_mapping(ExampleField()) == {"type": "string"}


def test_jsonschema_type_mapping_missing(spec):
    converter = ExtendedOpenAPIConverter("3.0.2", lambda _: None, spec)

    assert converter.jsonschema_type_mapping(fields.Field()) == {}
