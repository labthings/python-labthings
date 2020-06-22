from flask.views import MethodView
from flask import request
from werkzeug.wrappers import Response as ResponseBase
from werkzeug.exceptions import BadRequest

from collections import OrderedDict

from .args import use_args
from .marshalling import marshal_with

from ..utilities import unpack
from ..representations import DEFAULT_REPRESENTATIONS
from ..find import current_labthing
from ..event import PropertyStatusEvent
from ..schema import Schema, ActionSchema, build_action_schema

from labthings.core.tasks import taskify

from gevent.timeout import Timeout

import logging

__all__ = ["MethodView", "View", "ActionView", "PropertyView"]


class View(MethodView):
    """
    A LabThing Resource class should make use of functions
    get(), put(), post(), and delete(), corresponding to HTTP methods.

    These functions will allow for automated documentation generation.

    Unlike MethodView, a LabThings View is opinionated, in that unless
    explicitally returning a Response object, all requests with be marshaled
    with the same schema, and all request arguments will be parsed with the same
    args schema
    """

    endpoint = None
    __apispec__ = {}

    schema: Schema = None
    args: dict = None
    tags: list = []
    docs: dict = {}
    title: None
    semtype: str = None

    responses: dict = {}

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

        # Set the default representations
        # TODO: Inherit from parent LabThing. See original flask_restful implementation
        self.representations = OrderedDict(DEFAULT_REPRESENTATIONS)

    @classmethod
    def get_responses(cls):
        return {200: cls.schema}.update(cls.responses)

    @classmethod
    def get_args(cls):
        return cls.args

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

        # Flask should ensure this is assersion never fails
        assert meth is not None, f"Unimplemented method {request.method!r}"

        # Inject request arguments if an args schema is defined
        if self.args:
            meth = use_args(self.args)(meth)

        # Marhal response if a response schema is defines
        if self.schema:
            meth = marshal_with(self.schema)(meth)

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
    __apispec__ = {"tags": {"actions"}}

    tags: list = ["actions"]
    safe: bool = False
    idempotent: bool = False

    @classmethod
    def get_responses(cls):
        """Build an output schema that includes the Action wrapper object"""
        return {201: build_action_schema(cls.schema, cls.args)}.update(cls.responses)

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)

        # Let base View handle non-POST requests
        if request.method != "POST":
            return View.dispatch_request(self, *args, **kwargs)

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

        # If the action returns quickly, and returns a valid Response, return it as-is
        if task.output and isinstance(task.output, ResponseBase):
            return self.represent_response(task.output)

        return self.represent_response((ActionSchema().dump(task), 201))


class PropertyView(View):
    __apispec__ = {"tags": {"properties"}}

    tags: list = ["properties"]

    @classmethod
    def get_args(cls):
        """Use the output schema for arguments, on Properties"""
        return cls.schema

    def dispatch_request(self, *args, **kwargs):
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            # FIXME: Sketchy as this breaks if the response is a generator/loop
            resp = View.dispatch_request(self, *args, **kwargs)

            property_value = self.get_value()
            property_name = getattr(self, "endpoint", None) or getattr(
                self, "__name__", "unknown"
            )

            if current_labthing():
                current_labthing().message(
                    PropertyStatusEvent(property_name), property_value,
                )

            return resp

        return View.dispatch_request(self, *args, **kwargs)
