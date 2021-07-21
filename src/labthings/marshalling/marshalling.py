from collections.abc import Mapping
from functools import wraps
from typing import Callable, Dict, Optional, Tuple, Union

from marshmallow import Schema as _Schema
from werkzeug.wrappers import Response as ResponseBase

from ..fields import Field
from ..schema import FieldSchema, Schema
from ..utilities import unpack


def schema_to_converter(
    schema: Union[Schema, Field, Dict[str, Union[Field, type]]]
) -> Optional[Callable]:
    """Convert a schema into a converter function,
    which takes a value as an argument and returns
    marshalled data

    :param schema: Input schema

    """
    if isinstance(schema, Mapping):
        # Please ignore the pylint disable below,
        # GeneratedSchema definitely does have a `dump` member
        # pylint: disable=no-member
        return Schema.from_dict(schema)().dump
    # Case of schema as a single Field
    elif isinstance(schema, Field):
        return FieldSchema(schema).dump
    # Case of schema as a Schema
    elif isinstance(schema, _Schema):
        return schema.dump
    else:
        return None


def marshal(response: Union[Tuple, ResponseBase], converter: Callable):
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
    def __init__(self, schema: Union[Schema, Field, Dict[str, Union[Field, type]]]):
        """Decorator to format the return of a function with a Marshmallow schema

        :param schema: Marshmallow schema, field, or dict of Fields, describing
                the format of data to be returned by a View

        """
        self.schema = schema
        self.converter = schema_to_converter(self.schema)

    def __call__(self, f: Callable):
        # Wrapper function
        @wraps(f)
        def wrapper(*args, **kwargs):
            resp = f(*args, **kwargs)
            return marshal(resp, self.converter)

        return wrapper
