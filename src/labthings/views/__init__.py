from flask.views import MethodView, http_method_funcs
from flask import request
from werkzeug.wrappers import Response as ResponseBase
from werkzeug.exceptions import BadRequest

from .args import use_args
from .marshalling import marshal_with

from ..utilities import unpack, get_docstring, get_summary, merge
from ..representations import DEFAULT_REPRESENTATIONS
from ..find import current_labthing
from ..event import PropertyStatusEvent
from ..schema import Schema, ActionSchema, build_action_schema
from ..deque import Deque, resize_deque
from ..json.schemas import schema_to_json
from ..actions.pool import Pool
from .. import fields

import logging

__all__ = ["MethodView", "View", "ActionView", "PropertyView"]


class View(MethodView):
    """A LabThing Resource class should make use of functions
    get(), put(), post(), and delete(), corresponding to HTTP methods.
    
    These functions will allow for automated documentation generation.

    """

    endpoint = None  # Store the View endpoint for use in specs

    # Basic view spec metadata
    tags: list = []  # Custom tags the user can add
    title: None

    # Internal
    _cls_tags = set()  # Class tags that shouldn't be removed

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

        # Set the default representations
        self.representations = (
            current_labthing().representations
            if current_labthing()
            else DEFAULT_REPRESENTATIONS
        )

    @classmethod
    def get_apispec(cls):
        """Build a basic OpenAPI spec, containing only basic view metadata


        :returns: Minimal OpenAPI spec for the view class

        :rtype: [dict]

        """
        d = {}

        for method in http_method_funcs:
            if hasattr(cls, method):
                d[method] = {
                    "description": getattr(cls, "description", None)
                    or get_docstring(cls),
                    "summary": getattr(cls, "summary", None) or get_summary(cls),
                    "tags": list(cls.get_tags()),
                    "responses": {
                        "default": {
                            "description": "Unexpected error",
                            "content": {
                                "application/json": {
                                    "schema": schema_to_json(
                                        {
                                            "code": fields.Integer(),
                                            "message": fields.String(),
                                            "name": fields.String(),
                                        }
                                    )
                                }
                            },
                        }
                    },
                }
        return d

    @classmethod
    def get_tags(cls):
        """ """
        return cls._cls_tags.union(set(cls.tags))

    def get_value(self):
        """ """
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
        """

        :param *args: 
        :param **kwargs: 

        """
        meth = getattr(self, request.method.lower(), None)

        # If the request method is HEAD and we don't have a handler for it
        # retry with GET.
        if meth is None and request.method == "HEAD":
            meth = getattr(self, "get", None)

        # Generate basic response
        return self.represent_response(meth(*args, **kwargs))

    def represent_response(self, response):
        """Take the marshalled return value of a function
        and build a representation response

        :param response: 

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
    """ """

    # Data formatting
    schema: Schema = None  # Schema for Action response
    args: dict = None  # Schema for input arguments
    semtype: str = None  # Semantic type string

    # Spec overrides
    content_type = "application/json"  # Input contentType
    response_content_type = "application/json"  # Output contentType
    responses = {}  # Custom responses for invokeaction

    # Spec parameters
    safe: bool = False  # Does the action complete WITHOUT changing the Thing state
    idempotent: bool = False  # Can the action be performed idempotently

    # Action handling
    wait_for: int = 1  # Time in seconds to wait before returning the action as pending/running

    # Internal
    _cls_tags = {"actions"}
    _deque = Deque()  # Action queue
    _emergency_pool = Pool()

    def get(self):
        """ """
        queue_schema = build_action_schema(self.schema, self.args)(many=True)
        return queue_schema.dump(self._deque)

    @classmethod
    def get_apispec(cls):
        """Build an OpenAPI spec for the Action view


        :returns: OpenAPI spec for the view class

        :rtype: [dict]

        """
        class_args = schema_to_json(cls.args)
        action_json_schema = schema_to_json(build_action_schema(cls.schema, cls.args)())
        queue_json_schema = schema_to_json(
            build_action_schema(cls.schema, cls.args)(many=True)
        )
        class_json_schema = schema_to_json(cls.schema)

        # Get basic view spec
        d = super(ActionView, cls).get_apispec()
        # Add in Action spec
        d = merge(
            d,
            {
                "post": {
                    "requestBody": {
                        "content": {
                            cls.content_type: (
                                {"schema": class_args} if class_args else {}
                            )
                        }
                    },
                    "responses": {
                        # Responses like images must be added as 200 responses with cls.responses = {200: {...}}
                        200: {
                            "description": "Action completed immediately",
                            # Allow customising 200 (immediate response) content type
                            "content": {
                                cls.response_content_type: (
                                    {"schema": action_json_schema}
                                    if action_json_schema
                                    else {}
                                )
                            },
                        },
                        201: {
                            "description": "Action started",
                            # Our POST 201 MUST be application/json
                            "content": {
                                "application/json": (
                                    {"schema": action_json_schema}
                                    if action_json_schema
                                    else {}
                                )
                            },
                        },
                    },
                },
                "get": {
                    "responses": {
                        # Our GET 200 MUST be application/json
                        200: {
                            "description": "Action queue",
                            "content": {
                                "application/json": (
                                    {"schema": queue_json_schema}
                                    if queue_json_schema
                                    else {}
                                )
                            },
                        }
                    },
                },
            },
        )
        # Enable custom responses from POST
        d["post"]["responses"].update(cls.responses)
        return d

    def dispatch_request(self, *args, **kwargs):
        """

        :param *args: 
        :param **kwargs: 

        """
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

        # Try to find a pool on the current LabThing, but fall back to Views emergency pool
        pool = (
            current_labthing().actions if current_labthing() else self._emergency_pool
        )
        # Make a task out of the views `post` method
        task = pool.spawn(meth, *args, **kwargs)

        # Keep a copy of the raw, unmarshalled JSON input in the task
        try:
            task.input = request.json
        except BadRequest:
            task.input = None

        # Wait up to 2 second for the action to complete or error
        try:
            task.get(block=True, timeout=self.wait_for)
        except TimeoutError:
            pass

        # Log the action to the view's deque
        self._deque.append(task)

        # If the action returns quickly, and returns a valid Response, return it as-is
        if task.output and isinstance(task.output, ResponseBase):
            return self.represent_response(task.output, 200)

        return self.represent_response((ActionSchema().dump(task), 201))


class PropertyView(View):
    """ """

    # Data formatting
    schema: Schema = None  # Schema for input AND output
    semtype: str = None  # Semantic type string

    # Spec overrides
    content_type = "application/json"  # Input and output contentType
    responses = {}  # Custom responses for all interactions

    # Internal
    _cls_tags = {"properties"}

    @classmethod
    def get_apispec(cls):
        """Build an OpenAPI spec for the Property view


        :returns: OpenAPI spec for the view class

        :rtype: [dict]

        """
        class_json_schema = schema_to_json(cls.schema) if cls.schema else None

        # Get basic view spec
        d = super(PropertyView, cls).get_apispec()

        # Add in writeproperty methods
        for method in ("put", "post"):
            if hasattr(cls, method):
                d[method] = merge(
                    d.get(method, {}),
                    {
                        "requestBody": {
                            "content": {
                                cls.content_type: (
                                    {"schema": class_json_schema}
                                    if class_json_schema
                                    else {}
                                )
                            }
                        },
                        "responses": {
                            200: {
                                "content": {
                                    cls.content_type: (
                                        {"schema": class_json_schema}
                                        if class_json_schema
                                        else {}
                                    )
                                },
                                "description": "Write property",
                            }
                        },
                    },
                )

        # Add in readproperty methods
        if hasattr(cls, "get"):
            d["get"] = merge(
                d.get("get", {}),
                {
                    "responses": {
                        200: {
                            "content": {
                                cls.content_type: (
                                    {"schema": class_json_schema}
                                    if class_json_schema
                                    else {}
                                )
                            },
                            "description": "Read property",
                        }
                    },
                },
            )

        # Enable custom responses from all methods
        for method in d.keys():
            d[method]["responses"].update(cls.responses)

        return d

    def dispatch_request(self, *args, **kwargs):
        """

        :param *args: 
        :param **kwargs: 

        """
        meth = getattr(self, request.method.lower(), None)

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
