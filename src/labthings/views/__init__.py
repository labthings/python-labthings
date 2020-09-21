from collections import OrderedDict
import datetime
import threading

from flask import abort, request
from flask.views import MethodView
from werkzeug.exceptions import BadRequest
from werkzeug.wrappers import Response as ResponseBase

from ..actions.pool import Pool
from ..deque import Deque
from ..find import current_labthing
from ..marshalling import marshal_with, use_args
from ..representations import DEFAULT_REPRESENTATIONS
from ..schema import ActionSchema, EventSchema, Schema, build_action_schema
from ..utilities import unpack
from . import builder, op

__all__ = ["MethodView", "View", "ActionView", "PropertyView", "op", "builder"]


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

        # Set the default representations
        self.representations = (
            current_labthing().representations
            if current_labthing()
            else DEFAULT_REPRESENTATIONS
        )

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
        return response

    def _find_request_method(self):
        meth = getattr(self, request.method.lower(), None)
        if meth is None and request.method == "HEAD":
            meth = getattr(self, "get", None)

        return meth

    def dispatch_request(self, *args, **kwargs):
        """

        :param *args:
        :param **kwargs:

        """
        meth = self._find_request_method()

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
    wait_for: int = (
        1  # Time in seconds to wait before returning the action as pending/running
    )
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

    def dispatch_request(self, *args, **kwargs):
        """

        :param *args:
        :param **kwargs:

        """
        meth = self._find_request_method()

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
        task = pool.spawn(self.endpoint, meth, *args, **kwargs)
        # Optionally override the threads default_stop_timeout
        if self.default_stop_timeout is not None:
            task.default_stop_timeout = self.default_stop_timeout

        # Wait up to 2 second for the action to complete or error
        try:
            task.get(block=True, timeout=self.wait_for)
        except TimeoutError:
            pass

        # Log the action to the view's deque
        self._deque.append(task)

        # If the action returns quickly, and returns a valid Response, return it as-is
        if task.output and isinstance(task.output, ResponseBase):
            return self.represent_response((task.output, 200))

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
    _opmap = {
        "readproperty": "get",
        "writeproperty": "put",
    }  # Mapping of Thing Description ops to class methods
    _cls_tags = {"properties"}

    def dispatch_request(self, *args, **kwargs):
        """

        :param *args:
        :param **kwargs:

        """
        meth = self._find_request_method()

        # POST and PUT methods can be used to write properties
        # In all other cases, ignore arguments
        if request.method in ("PUT", "POST") and self.schema:
            meth = use_args(self.schema)(meth)

        # All methods should serialise properties
        if self.schema:
            meth = marshal_with(self.schema)(meth)

        # Generate basic response
        return self.represent_response(meth(*args, **kwargs))


class EventView(View):
    """ """

    # Data formatting
    schema: Schema = None  # Schema for Event data
    semtype: str = None  # Semantic type string

    # Spec overrides
    content_type = "application/json"  # Input contentType

    # Internal
    _opmap = {
        "subscribeevent": "get",
    }  # Mapping of Thing Description ops to class methods
    _cls_tags = {"events"}
    _deque = Deque()  # Action queue

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def get(cls):
        """
        Default method for GET requests. Returns the action queue (including already finished actions) for this action
        """
        return EventSchema(many=True).dump(cls._deque)

    @classmethod
    def emit(cls, data):
        d = {"timestamp": datetime.datetime.now()}
        if data:
            if cls.schema:
                d["data"] = cls.schema.dump(data)
            else:
                d["data"] = data
        cls._deque.append(d)
