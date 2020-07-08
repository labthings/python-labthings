from flask.views import MethodView, http_method_funcs
from flask import request
from werkzeug.wrappers import Response as ResponseBase
from werkzeug.exceptions import BadRequest

from collections import OrderedDict

from .args import use_args
from .marshalling import marshal_with

from ..utilities import unpack, get_docstring, get_summary
from ..representations import DEFAULT_REPRESENTATIONS
from ..find import current_labthing
from ..event import PropertyStatusEvent
from ..schema import Schema, ActionSchema, build_action_schema
from ..tasks import taskify
from ..deque import Deque, resize_deque
from ..json.schemas import schema_to_json

from gevent.timeout import Timeout

import logging

__all__ = ["MethodView", "View", "ActionView", "PropertyView"]


class View(MethodView):
    """
    A LabThing Resource class should make use of functions
    get(), put(), post(), and delete(), corresponding to HTTP methods.

    These functions will allow for automated documentation generation.
    """

    endpoint = None
    semtype: str = None

    tags: list = []  # Custom tags the user can add
    _cls_tags = set()  # Class tags that shouldn't be removed
    title: None

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

        # Set the default representations
        # TODO: Inherit from parent LabThing. See original flask_restful implementation
        self.representations = OrderedDict(DEFAULT_REPRESENTATIONS)

    @classmethod
    def get_apispec(cls):
        d = {}

        for method in http_method_funcs:
            if hasattr(cls, method):
                d[method] = {
                    "description": getattr(cls, "description", None)
                    or get_docstring(cls),
                    "summary": getattr(cls, "summary", None) or get_summary(cls),
                    "tags": list(cls.get_tags()),
                }

        # Enable custom responses from all methods
        if getattr(cls, "responses", None):
            for method in d.keys():
                d[method]["responses"] = getattr(cls, "responses")
        return d

    @classmethod
    def get_tags(cls):
        return cls._cls_tags.union(set(cls.tags))

    def get_value(self):
        get_method = getattr(self, "get", None)  # Look for this views GET method
        if get_method is None:
            return None
        if not callable(get_method):
            raise TypeError("Attribute 'get' of View must be a callable")
        response = get_method()  # pylint: disable=not-callable
        if isinstance(response, ResponseBase):  # Pluck useful data out of HTTP response
            return response.json if response.json else response.data
        else:  # Unless somehow an HTTP response isn't returned...
            return response

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)

        # If the request method is HEAD and we don't have a handler for it
        # retry with GET.
        if meth is None and request.method == "HEAD":
            meth = getattr(self, "get", None)

        # Generate basic response
        return self.represent_response(meth(*args, **kwargs))

    def represent_response(self, response):
        """
        Take the marshalled return value of a function
        and build a representation response
        """
        if isinstance(response, ResponseBase):  # There may be a better way to test
            return response

        representations = self.representations or OrderedDict()

        # noinspection PyUnresolvedReferences
        mediatype = request.accept_mimetypes.best_match(representations, default=None)
        if mediatype in representations:
            data, code, headers = unpack(response)
            response = representations[mediatype](data, code, headers)
            response.headers["Content-Type"] = mediatype
            return response
        return response


class ActionView(View):
    # TODO: Better support for overriding content type
    # TODO: Better support for custom 200 responses

    # Data formatting
    schema: Schema = None
    args: dict = None
    semtype: str = None

    # Spec overrides
    responses = {}  # Custom responses for invokeaction

    # Spec parameters
    safe: bool = False
    idempotent: bool = False

    # Internal
    _cls_tags = {"actions"}
    _deque = Deque()  # Action queue

    def get(self):
        queue_schema = build_action_schema(self.schema, self.args)(many=True)
        return queue_schema.dump(self._deque)

    @classmethod
    def get_apispec(cls):
        class_args = schema_to_json(cls.args)
        action_json_schema = schema_to_json(build_action_schema(cls.schema, cls.args)())
        queue_json_schema = schema_to_json(
            build_action_schema(cls.schema, cls.args)(many=True)
        )
        class_json_schema = schema_to_json(cls.schema)
        d = {
            "post": {
                "description": getattr(cls, "description", None) or get_docstring(cls),
                "summary": getattr(cls, "summary", None) or get_summary(cls),
                "tags": list(cls.get_tags()),
                "requestBody": {
                    "content": {
                        "application/json": (
                            {"schema": class_args} if class_args else {}
                        )
                    }
                },
                "responses": {
                    # Our POST 201 will usually be application/json
                    201: {
                        "content_type": "application/json",
                        "description": "Action started",
                        **(
                            {"schema": action_json_schema} if action_json_schema else {}
                        ),
                    }
                },
            },
            "get": {
                "description": "Action queue",
                "summary": "Action queue",
                "tags": list(cls.get_tags()),
                "responses": {
                    # Our GET 200 will usually be application/json
                    200: {
                        "content_type": "application/json",
                        "description": "Action started",
                        **({"schema": queue_json_schema} if queue_json_schema else {}),
                    }
                },
            },
        }
        # Enable custom responses from POST
        d["post"]["responses"].update(cls.responses)
        return d

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)

        # Let base View handle non-POST requests
        if request.method != "POST":
            return View.dispatch_request(self, *args, **kwargs)

        # Inject request arguments if an args schema is defined
        if self.args:
            meth = use_args(self.args)(meth)

        # Marhal response if a response schema is defined
        if self.schema:
            meth = marshal_with(self.schema)(meth)

        # Make a task out of the views `post` method
        task = taskify(meth)(*args, **kwargs)

        # Keep a copy of the raw, unmarshalled JSON input in the task
        try:
            task.input = request.json
        except BadRequest:
            task.input = None

        # Wait up to 2 second for the action to complete or error
        try:
            task.get(block=True, timeout=1)
            logging.debug("Got Action response quickly")
        except Timeout:
            pass

        # Log the action to the view's deque
        self._deque.append(task)

        # If the action returns quickly, and returns a valid Response, return it as-is
        if task.output and isinstance(task.output, ResponseBase):
            return self.represent_response(task.output, 200)

        return self.represent_response((ActionSchema().dump(task), 201))


class PropertyView(View):
    schema: Schema = None
    semtype: str = None

    # Spec overrides
    responses = {}  # Custom responses for invokeaction

    _cls_tags = {"properties"}

    @classmethod
    def get_apispec(cls):
        d = {}
        class_json_schema = schema_to_json(cls.schema) if cls.schema else None

        # writeproperty methods
        for method in ("put", "post"):
            if hasattr(cls, method):
                d[method] = {
                    "description": getattr(cls, "description", None)
                    or get_docstring(cls),
                    "summary": getattr(cls, "summary", None) or get_summary(cls),
                    "tags": list(cls.get_tags()),
                    "requestBody": {
                        "content": {
                            "application/json": (
                                {"schema": class_json_schema}
                                if class_json_schema
                                else {}
                            )
                        }
                    },
                    "responses": {
                        200: {
                            "content_type": "application/json",
                            "description": "Write property",
                            **(
                                {"schema": class_json_schema}
                                if class_json_schema
                                else {}
                            ),
                        }
                    },
                }

        if hasattr(cls, "get"):
            d["get"] = {
                "description": getattr(cls, "description", None) or get_docstring(cls),
                "summary": getattr(cls, "summary", None) or get_summary(cls),
                "tags": list(cls.get_tags()),
                "responses": {
                    200: {
                        "content_type": "application/json",
                        "description": "Read property",
                        **({"schema": class_json_schema} if class_json_schema else {}),
                    }
                },
            }

        # Enable custom responses from all methods
        for method in d.keys():
            d[method]["responses"].update(cls.responses)

        return d

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)

        # Flask should ensure this is assersion never fails
        assert meth is not None, f"Unimplemented method {request.method!r}"

        # If the request method is HEAD and we don't have a handler for it
        # retry with GET.
        if meth is None and request.method == "HEAD":
            meth = getattr(self, "get", None)

        # POST and PUT methods can be used to write properties
        # In all other cases, ignore arguments
        if request.method in ("PUT", "POST") and self.schema:
            meth = use_args(self.schema)(meth)

        # All methods should serialise properties
        if self.schema:
            meth = marshal_with(self.schema)(meth)

        # Generate basic response
        resp = self.represent_response(meth(*args, **kwargs))

        # Emit property event
        if request.method in ("POST", "PUT"):
            property_value = self.get_value()
            property_name = getattr(self, "endpoint", None) or getattr(
                self, "__name__", "unknown"
            )

            if current_labthing():
                current_labthing().message(
                    PropertyStatusEvent(property_name), property_value,
                )

        return resp
