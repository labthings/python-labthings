from webargs import flaskparser
from functools import wraps, update_wrapper
from flask import make_response
from http import HTTPStatus

from ..core.utilities import rupdate

from .spec import update_spec
from .schema import TaskSchema


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
        """
        :param schema: a dict of whose keys will make up the final
                        serialized response output
        """
        self.schema = schema
        self.code = code

    def __call__(self, f):
        # Pass params to call function attribute for external access
        update_spec(f, {"_schema": {self.code: self.schema}})
        # Wrapper function
        @wraps(f)
        def wrapper(*args, **kwargs):
            resp = f(*args, **kwargs)
            if isinstance(resp, tuple):
                data, code, headers = unpack(resp)
                return make_response(self.schema.jsonify(data), code, headers)
            else:
                return make_response(self.schema.jsonify(resp))

        return wrapper


def marshal_task(f):
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


def ThingAction(viewcls):
    # Pass params to call function attribute for external access
    update_spec(viewcls, {"tags": ["actions"]})
    update_spec(viewcls, {"_groups": ["actions"]})
    return viewcls


thing_action = ThingAction


def ThingProperty(viewcls):
    # Pass params to call function attribute for external access
    update_spec(viewcls, {"tags": ["properties"]})
    update_spec(viewcls, {"_groups": ["properties"]})
    return viewcls


thing_property = ThingProperty


class use_args(object):
    def __init__(self, schema, **kwargs):
        """
        Equivalent to webargs.flask_parser.use_args
        """
        self.schema = schema
        self.wrapper = flaskparser.use_args(schema, **kwargs)

    def __call__(self, f):
        # Pass params to call function attribute for external access
        update_spec(f, {"_params": self.schema})
        # Wrapper function
        update_wrapper(self.wrapper, f)
        return self.wrapper(f)


class use_kwargs(use_args):
    def __init__(self, schema, **kwargs):
        """
        Equivalent to webargs.flask_parser.use_kwargs
        """
        kwargs["as_kwargs"] = True
        use_args.__init__(self, schema, **kwargs)


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
            self.response_dict.update({
                "responses": {
                    self.code: {
                        "content": {self.mimetype: {}}
                    }
                }
            })

    def __call__(self, f):
        # Pass params to call function attribute for external access
        update_spec(f, self.response_dict)
        return f
