from apispec.ext.marshmallow import (
    MarshmallowPlugin as _MarshmallowPlugin,
    OpenAPIConverter,
)
from labthings.server.fields import Bytes as BytesField


class ExtendedOpenAPIConverter(OpenAPIConverter):
    field_mapping = OpenAPIConverter.field_mapping
    field_mapping.update({BytesField: ("string", None)})

    def init_attribute_functions(self, *args, **kwargs):
        OpenAPIConverter.init_attribute_functions(self, *args, **kwargs)
        self.attribute_functions.append(self.bytes2json)

    def bytes2json(self, field, **kwargs):
        ret = {}
        if isinstance(field, BytesField):
            ret.update({"contentEncoding": "base64"})
        return ret


class MarshmallowPlugin(_MarshmallowPlugin):
    Converter = ExtendedOpenAPIConverter
