from apispec.ext.marshmallow import MarshmallowPlugin as _MarshmallowPlugin
from .converter import ExtendedOpenAPIConverter


class MarshmallowPlugin(_MarshmallowPlugin):
    """ """
    Converter = ExtendedOpenAPIConverter
