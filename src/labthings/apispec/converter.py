from apispec.ext.marshmallow import OpenAPIConverter
from ..fields import Bytes as BytesField


class ExtendedOpenAPIConverter(OpenAPIConverter):
    field_mapping = OpenAPIConverter.field_mapping

    def init_attribute_functions(self, *args, **kwargs):
        OpenAPIConverter.init_attribute_functions(self, *args, **kwargs)
        self.attribute_functions.append(self.bytes2json)

    def bytes2json(self, field, **kwargs):
        ret = {}
        if isinstance(field, BytesField):
            ret.update(BytesField()._jsonschema_type_mapping())
        return ret
