from functools import wraps

from ..schema import Schema, FieldSchema
from ..fields import Field

from ..utilities import unpack

from werkzeug.wrappers import Response as ResponseBase

from collections.abc import Mapping
from marshmallow import Schema as _Schema


def schema_to_converter(schema):
    """Convert a schema into a converter function,
    which takes a value as an argument and returns
    marshalled data

    :param schema: Input schema

    """
    if isinstance(schema, Mapping):
        return Schema.from_dict(schema)().dump
    # Case of schema as a single Field
    elif isinstance(schema, Field):
        return FieldSchema(schema).dump
    # Case of schema as a Schema
    elif isinstance(schema, _Schema):
        return schema.dump
    else:
        return None


def marshal(response, converter):
    """

    :param response: 
    :param converter: 

    """
    if isinstance(response, ResponseBase):
        response.data = converter(response.data)
        return response
    elif isinstance(response, tuple):
        response, code, headers = unpack(response)
        return (converter(response), code, headers)
    return converter(response)


class marshal_with:
    def __init__(self, schema):
        """Decorator to format the return of a function with a Marshmallow schema

        :param schema: Marshmallow schema, field, or dict of Fields, describing
                the format of data to be returned by a View

        """
        self.schema = schema
        self.converter = schema_to_converter(self.schema)

    def __call__(self, f):
        # Wrapper function
        @wraps(f)
        def wrapper(*args, **kwargs):
            resp = f(*args, **kwargs)
            return marshal(resp, self.converter)

        return wrapper
