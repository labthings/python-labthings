from webargs import flaskparser
from functools import wraps, update_wrapper
from flask import make_response, abort, request
from http import HTTPStatus
from marshmallow.exceptions import ValidationError
from collections import Mapping

from .spec.utilities import update_spec
from .schema import TaskSchema, Schema, FieldSchema
from .fields import Field
from .view import View

import logging

# Useful externals to have included here
from marshmallow import pre_dump, pre_load


def unpack(value):
    """Return a three tuple of data, code, and headers"""
    if not isinstance(value, tuple):
        return value, 200, {}

    try:
        data, code, headers = value
        return data, code, headers
    except ValueError:
        pass

    try:
        data, code = value
        return data, code, {}
    except ValueError:
        pass

    return value, 200, {}


class marshal_with(object):
    def __init__(self, schema, code=200):
        """Decorator to format the response of a View with a Marshmallow schema

        Args:
            schema: Marshmallow schema, field, or dict of Fields, describing
                the format of data to be returned by a View
        """
        self.schema = schema
        self.code = code

        if isinstance(self.schema, Mapping):
            self.converter = Schema.from_dict(self.schema)().jsonify
        elif isinstance(self.schema, Field):
            self.converter = FieldSchema(self.schema).jsonify
        elif isinstance(self.schema, Schema):
            self.converter = self.schema.jsonify
        else:
            raise TypeError(
                f"Unsupported schema type {type(self.schema)} for marshal_with"
            )

    def __call__(self, f):
        # Pass params to call function attribute for external access
        update_spec(f, {"_schema": {self.code: self.schema}})
        # Wrapper function
        @wraps(f)
        def wrapper(*args, **kwargs):
            resp = f(*args, **kwargs)
            if isinstance(resp, tuple):
                data, code, headers = unpack(resp)
                return make_response(self.converter(data), code, headers)
            else:
                return make_response(self.converter(resp))

        return wrapper


def marshal_task(f):
    """Decorator to format the response of a View with the standard Task schema"""

    # Pass params to call function attribute for external access
    update_spec(f, {"responses": {201: {"description": "Task started successfully"}}})
    update_spec(f, {"_schema": {201: TaskSchema()}})
    # Wrapper function
    @wraps(f)
    def wrapper(*args, **kwargs):
        resp = f(*args, **kwargs)
        if isinstance(resp, tuple):
            data, code, headers = unpack(resp)
            return make_response(TaskSchema().jsonify(data), code, headers)
        else:
            return make_response(TaskSchema().jsonify(resp))

    return wrapper


def ThingAction(viewcls: View):
    """Decorator to tag a view as a Thing Action

    Args:
        viewcls (View): View class to tag as an Action

    Returns:
        View: View class with Action spec tags
    """
    # Pass params to call function attribute for external access
    update_spec(viewcls, {"tags": ["actions"]})
    update_spec(viewcls, {"_groups": ["actions"]})
    return viewcls


thing_action = ThingAction


def ThingProperty(viewcls):
    """Decorator to tag a view as a Thing Property

    Args:
        viewcls (View): View class to tag as an Property

    Returns:
        View: View class with Property spec tags
    """
    # Pass params to call function attribute for external access
    update_spec(viewcls, {"tags": ["properties"]})
    update_spec(viewcls, {"_groups": ["properties"]})
    return viewcls


thing_property = ThingProperty


class PropertySchema(object):
    def __init__(self, schema, code=200):
        """
        :param schema: a dict of whose keys will make up the final
                        serialized response output
        """
        self.schema = schema
        self.code = code

    def __call__(self, viewcls):
        update_spec(viewcls, {"_propertySchema": self.schema})

        if hasattr(viewcls, "get") and callable(viewcls.get):
            viewcls.get = marshal_with(self.schema, code=self.code)(viewcls.get)

        if hasattr(viewcls, "post") and callable(viewcls.post):
            viewcls.post = marshal_with(self.schema, code=self.code)(viewcls.post)
            viewcls.post = use_args(self.schema)(viewcls.post)

        if hasattr(viewcls, "put") and callable(viewcls.put):
            viewcls.put = marshal_with(self.schema, code=self.code)(viewcls.put)
            viewcls.put = use_args(self.schema)(viewcls.put)

        return viewcls


class use_body(object):
    """
    Gets the request body as a single value and adds it as a positional argument
    """

    def __init__(self, schema, **kwargs):
        self.schema = schema

    def __call__(self, f):
        # Pass params to call function attribute for external access
        update_spec(f, {"_params": self.schema})

        # Wrapper function
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get data from request
            data = request.data or None

            # If no data is there
            if not data:
                # If data is required
                if self.schema.required == True:
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


class use_args(object):
    """
    Equivalent to webargs.flask_parser.use_args
    """

    def __init__(self, schema, **kwargs):
        self.schema = schema

        if isinstance(schema, Field):
            self.wrapper = use_body(schema, **kwargs)
        else:
            self.wrapper = flaskparser.use_args(schema, **kwargs)

    def __call__(self, f):
        # Pass params to call function attribute for external access
        update_spec(f, {"_params": self.schema})
        # Wrapper function
        update_wrapper(self.wrapper, f)
        return self.wrapper(f)


class Doc(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, f):
        # Pass params to call function attribute for external access
        update_spec(f, self.kwargs)
        return f


doc = Doc


class Tag(object):
    def __init__(self, tags):
        if isinstance(tags, str):
            self.tags = [tags]
        elif isinstance(tags, list) and all([isinstance(e, str) for e in tags]):
            self.tags = tags
        else:
            raise TypeError("Tags must be a string or list of strings")

    def __call__(self, f):
        # Pass params to call function attribute for external access
        update_spec(f, {"tags": self.tags})
        return f


tag = Tag


class doc_response(object):
    def __init__(self, code, description=None, mimetype=None, **kwargs):
        self.code = code
        self.description = description
        self.kwargs = kwargs
        self.mimetype = mimetype

        self.response_dict = {
            "responses": {
                self.code: {
                    "description": self.description or HTTPStatus(self.code).phrase,
                    **self.kwargs,
                }
            }
        }

        if self.mimetype:
            self.response_dict.update(
                {"responses": {self.code: {"content": {self.mimetype: {}}}}}
            )

    def __call__(self, f):
        # Pass params to call function attribute for external access
        update_spec(f, self.response_dict)
        return f
