from apispec.ext.marshmallow import OpenAPIConverter


class ExtendedOpenAPIConverter(OpenAPIConverter):
    field_mapping = OpenAPIConverter.field_mapping

    def init_attribute_functions(self, *args, **kwargs):
        OpenAPIConverter.init_attribute_functions(self, *args, **kwargs)
        self.attribute_functions.append(self.bytes2json)

    def bytes2json(self, field, **kwargs):
        ret = {}
        if hasattr(field, "_jsonschema_type_mapping"):
            schema = field._jsonschema_type_mapping()
            ret.update(schema)
        return ret
