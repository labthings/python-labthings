from flask.views import MethodView, http_method_funcs
from flask import request, abort
from werkzeug.wrappers import Response as ResponseBase
from werkzeug.exceptions import BadRequest

from .args import use_args
from .marshalling import marshal_with

from . import op
from .interactions import Property, Action

from ..utilities import unpack, get_docstring, get_summary, merge
from ..representations import DEFAULT_REPRESENTATIONS
from ..find import current_labthing
from ..schema import Schema, ActionSchema, build_action_schema
from ..deque import Deque, resize_deque
from ..json.schemas import schema_to_json
from ..actions.pool import Pool

from .. import fields

import logging


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
    _opmap = {}  # Mapping of Thing Description ops to class methods

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

        self.representations = (
            current_labthing().representations
            if current_labthing()
            else DEFAULT_REPRESENTATIONS
        )

    def dispatch_request(self, *args, **kwargs):
        """
        :param *args: 
        :param **kwargs: 
        """
        meth = getattr(self, request.method.lower(), None)
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

        representations = self.representations

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
    default_stop_timeout: int = None  # Time in seconds to wait for the action thread to end after a stop request before terminating it forcefully

    # Internal
    _opmap = {
        "invokeaction": "post"
    }  # Mapping of Thing Description ops to class methods
    _cls_tags = {"actions"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def get(cls):
        """
        Default method for GET requests. 
        Returns the action queue (including already finished actions) for this action
        """
        queue_schema = build_action_schema(cls.schema, cls.args)(many=True)
        return queue_schema.dump(cls._deque)

    @classmethod
    def as_interaction(cls, endpoint=None):
        action = Action(
            endpoint or cls.__name__,
            None,
            None,
            schema=cls.schema,
            args=cls.args,
            semtype=cls.semtype,
            safe=cls.safe,
            idempotent=cls.idempotent,
        )
        action.content_type = cls.content_type
        action.response_content_type = cls.response_content_type
        for thing_op, http_meth in cls._opmap.items():
            setattr(action, thing_op, getattr(cls, http_meth))
            action._methodmap[http_meth] = thing_op

        return action


class PropertyView(View):
    """ """

    # Data formatting
    schema: Schema = None  # Schema for input AND output
    semtype: str = None  # Semantic type string

    # Spec overrides
    content_type = "application/json"  # Input and output contentType
    responses = {}  # Custom responses for all interactions

    # Internal
    _opmap = {
        "readproperty": "get",
        "writeproperty": "put",
    }  # Mapping of Thing Description ops to class methods
    _cls_tags = {"properties"}

    @classmethod
    def _is_readonly(cls):
        return hasattr(cls, cls._opmap.get("writeproperty"))

    @classmethod
    def as_interaction(cls, endpoint=None):
        prop = Property(
            endpoint or cls.__name__,
            None,
            None,
            schema=cls.schema,
            semtype=cls.semtype,
            readonly=cls._is_readonly(),
        )
        prop.content_type = cls.content_type
        for thing_op, http_meth in cls._opmap.items():
            setattr(prop, thing_op, getattr(cls, http_meth))
            prop._methodmap[http_meth] = thing_op

        return prop
