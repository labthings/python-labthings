from webargs import flaskparser
from functools import wraps, update_wrapper
from flask import abort, request
from werkzeug.wrappers import Response as ResponseBase
from http import HTTPStatus
from marshmallow.exceptions import ValidationError
from collections.abc import Mapping

from marshmallow import Schema as _Schema

from .spec.utilities import update_spec, tag_spec
from .schema import TaskSchema, Schema, FieldSchema
from .fields import Field
from .view import View
from .find import current_labthing
from .utilities import unpack

from labthings.core.tasks.pool import TaskThread
from labthings.core.utilities import merge

import logging


class marshal_with:
    def __init__(self, schema, code=200):
        """Decorator to format the return of a function with a Marshmallow schema

        Args:
            schema: Marshmallow schema, field, or dict of Fields, describing
                the format of data to be returned by a View
        """
        self.schema = schema
        self.code = code

        if isinstance(self.schema, Mapping):
            self.converter = Schema.from_dict(self.schema)().dump
        elif isinstance(self.schema, Field):
            self.converter = FieldSchema(self.schema).dump
        elif isinstance(self.schema, _Schema):
            self.converter = self.schema.dump
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
            if isinstance(resp, ResponseBase):
                resp.data = self.converter(resp.data)
                return resp
            elif isinstance(resp, tuple):
                resp, code, headers = unpack(resp)
                return (self.converter(resp), code, headers)
            else:
                resp, code, headers = resp, 200, {}
            return (self.converter(resp), code, headers)

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
            resp, code, headers = unpack(resp)
        else:
            resp, code, headers = resp, 201, {}

        if not isinstance(resp, TaskThread):
            raise TypeError(
                f"Function {f.__name__} expected to return a TaskThread object, but instead returned a {type(resp).__name__}. If it does not return a task, remove the @marshall_task decorator from {f.__name__}."
            )
        return (TaskSchema().dump(resp), code, headers)

    return wrapper


def ThingAction(viewcls: View):
    """Decorator to tag a view as a Thing Action

    Args:
        viewcls (View): View class to tag as an Action

    Returns:
        View: View class with Action spec tags
    """
    # Update Views API spec
    tag_spec(viewcls, "actions")
    return viewcls


thing_action = ThingAction


def Safe(viewcls: View):
    """Decorator to tag a view or function as being safe

    Args:
        viewcls (View): View class to tag as Safe

    Returns:
        View: View class with Safe spec tags
    """
    # Update Views API spec
    update_spec(viewcls, {"_safe": True})
    return viewcls


safe = Safe


def Idempotent(viewcls: View):
    """Decorator to tag a view or function as being idempotent

    Args:
        viewcls (View): View class to tag as idempotent

    Returns:
        View: View class with idempotent spec tags
    """
    # Update Views API spec
    update_spec(viewcls, {"_idempotent": True})
    return viewcls


idempotent = Idempotent


def ThingProperty(viewcls):
    """Decorator to tag a view as a Thing Property

    Args:
        viewcls (View): View class to tag as an Property

    Returns:
        View: View class with Property spec tags
    """

    def property_notify(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            # Call the update function first to update property value
            original_response = func(*args, **kwargs)

            # Once updated, then notify all subscribers
            subscribers = getattr(current_labthing(), "subscribers", [])
            for sub in subscribers:
                sub.property_notify(viewcls)
            return original_response

        return wrapped

    if hasattr(viewcls, "post") and callable(viewcls.post):
        viewcls.post = property_notify(viewcls.post)

    if hasattr(viewcls, "put") and callable(viewcls.put):
        viewcls.put = property_notify(viewcls.put)

    # Update Views API spec
    tag_spec(viewcls, "properties")
    return viewcls


thing_property = ThingProperty


class PropertySchema:
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


class use_body:
    """Gets the request body as a single value and adds it as a positional argument"""

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


class use_args:
    """Equivalent to webargs.flask_parser.use_args"""

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


class Doc:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, f):
        # Pass params to call function attribute for external access
        update_spec(f, self.kwargs)
        return f


doc = Doc


class Tag:
    def __init__(self, tags):
        self.tags = tags

    def __call__(self, f):
        # Pass params to call function attribute for external access
        tag_spec(f, self.tags)
        return f


tag = Tag


class doc_response:
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
            self.response_dict = merge(
                self.response_dict,
                {
                    "responses": {self.code: {"content": {self.mimetype: {}}}},
                    "_content_type": self.mimetype,
                },
            )

    def __call__(self, f):
        # Pass params to call function attribute for external access
        update_spec(f, self.response_dict)
        return f
