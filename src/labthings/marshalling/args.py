import logging
from functools import update_wrapper, wraps
from typing import Callable, Mapping, Union

from flask import abort, request
from marshmallow.exceptions import ValidationError
from webargs import flaskparser

from ..fields import Field
from ..schema import FieldSchema, Schema


def use_body(schema: Field, **_) -> Callable:
    def inner(f: Callable):
        # Wrapper function
        @wraps(f)
        def wrapper(*args, **kwargs):
            """

            :param *args:
            :param **kwargs:

            """
            # Get data from request
            data = request.get_json(silent=True) or request.data or None

            # If no data is there
            if not data:
                # If data is required
                if schema.required:
                    # Abort
                    return abort(400)
                # Otherwise, look for the schema fields 'missing' property
                if schema.missing:
                    data = schema.missing

            # Serialize data if it exists
            if data:
                try:
                    data = FieldSchema(schema).deserialize(data)
                except ValidationError as e:
                    logging.error(e)
                    return abort(400)

            # Inject argument and return wrapped function
            return f(*args, data, **kwargs)

        return wrapper

    return inner


class use_args:
    """Equivalent to webargs.flask_parser.use_args"""

    def __init__(self, schema: Union[Schema, Field, Mapping[str, Field]], **kwargs):
        self.schema = schema

        if isinstance(schema, Field):
            self.wrapper = use_body(schema, **kwargs)
        else:
            self.wrapper = flaskparser.use_args(schema, **kwargs)

    def __call__(self, f: Callable):
        # Wrapper function
        update_wrapper(self.wrapper, f)
        return self.wrapper(f)
