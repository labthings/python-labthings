from flask.views import MethodView, http_method_funcs
from flask import request, abort
from werkzeug.wrappers import Response as ResponseBase
from werkzeug.exceptions import BadRequest

from .args import use_args
from .marshalling import marshal_with

from . import methods as op
from .interactions import Property, Action

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
    _deque = Deque()  # Action queue
    _emergency_pool = Pool()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def get(cls):
        """
        Default method for GET requests. Returns the action queue (including already finished actions) for this action
        """
        queue_schema = build_action_schema(cls.schema, cls.args)(many=True)
        return queue_schema.dump(cls._deque)


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
    def as_interaction(cls):
        prop = Property(cls.__name__, schema=cls.schema, semtype=cls.semtype)
        prop.content_type = cls.content_type
        for thing_op, http_meth in cls._opmap.items():
            setattr(prop, thing_op, cls.getattr(http_meth))
            prop._methodmap[http_meth] = thing_op
