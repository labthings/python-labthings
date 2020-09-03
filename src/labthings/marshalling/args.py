from webargs import flaskparser
from functools import wraps, update_wrapper
from flask import request, abort
from marshmallow.exceptions import ValidationError

from ..fields import Field
from ..schema import FieldSchema

import logging


class use_body:
    """Gets the request body as a single value and adds it as a positional argument"""

    def __init__(self, schema, **kwargs):
        self.schema = schema

    def __call__(self, f):
        # Wrapper function
        @wraps(f)
        def wrapper(*args, **kwargs):
            """

            :param *args: 
            :param **kwargs: 

            """
            # Get data from request
            data = request.data or None

            # If no data is there
            if not data:
                # If data is required
                if self.schema.required:
                    # Abort
                    return abort(400)
                # Otherwise, look for the schema fields 'missing' property
                if self.schema.missing:
                    data = self.schema.missing

            # Serialize data if it exists
            if data:
                try:
                    data = FieldSchema(self.schema).deserialize(data)
                except ValidationError as e:
                    logging.error(e)
                    return abort(400)

            # Inject argument and return wrapped function
            return f(*args, data, **kwargs)

        return wrapper


class use_args:
    """Equivalent to webargs.flask_parser.use_args"""

    def __init__(self, schema, **kwargs):
        self.schema = schema

        if isinstance(schema, Field):
            self.wrapper = use_body(schema, **kwargs)
        else:
            self.wrapper = flaskparser.use_args(schema, **kwargs)

    def __call__(self, f):
        # Wrapper function
        update_wrapper(self.wrapper, f)
        return self.wrapper(f)
