from typing import Callable, Dict, List, Union
from flask import request, abort
from flask.views import http_method_funcs
from werkzeug.wrappers import Response as ResponseBase
from werkzeug.exceptions import BadRequest

from .args import use_args
from .marshalling import marshal_with

from ..schema import Schema, ActionSchema, build_action_schema
from ..fields import Field
from ..semantics.base import Semantic

from ..deque import Deque
from ..find import current_labthing
from ..utilities import unpack
from ..representations import DEFAULT_REPRESENTATIONS
from ..actions.pool import Pool


class Interaction:
    def __init__(self, name: str):
        self.name = name
        self.endpoint = None

        self.content_type = "application/json"  # Input contentType
        self.response_content_type = "application/json"  # Output contentType

        self._methodmap = {}
        # Set the default representations
        self._representations = (
            current_labthing().representations
            if current_labthing()
            else DEFAULT_REPRESENTATIONS
        )

    @property
    def methods(self):
        allowed_methods = set()
        for http_meth in http_method_funcs:
            if http_meth in self._methodmap and hasattr(
                self, self._methodmap.get(http_meth)
            ):
                allowed_methods.add(http_meth)
        return allowed_methods

    def _represent_response(self, response):
        """Take the marshalled return value of a function
        and build a representation response

        :param response:

        """
        if isinstance(response, ResponseBase):  # There may be a better way to test
            return response

        representations = self._representations

        # noinspection PyUnresolvedReferences
        mediatype = request.accept_mimetypes.best_match(representations, default=None)
        if mediatype in representations:
            data, code, headers = unpack(response)
            response = representations[mediatype](data, code, headers)
            response.headers["Content-Type"] = mediatype
            return response
        return response

    def _find_request_method(self):
        request_meth = request.method.lower()
        print("Running _find_request_method")
        if request_meth == "get" and request.environ.get("wsgi.websocket"):
            response_meth = self._methodmap.get("websocket", None)
            if response_meth is None:
                abort(400, "Unable to upgrade websocket connection")
        else:
            response_meth = self._methodmap.get(request_meth, None)
            if response_meth is None:
                abort(405)

        return response_meth

    def dispatch_request(self, *args, **kwargs):
        """

        :param *args: 
        :param **kwargs: 

        """
        print("Interaction.dispatch_request")
        method_name = self._find_request_method()
        method = getattr(self, method_name, None)

        # Generate basic response
        return self._represent_response(method(*args, **kwargs))


class Property(Interaction):
    def __init__(
        self,
        name: str,
        writeproperty_forwarder: Callable,
        readproperty_forwarder: Callable,
        readonly: bool = False,
        description: str = "",
        tags: List[str] = [],
        schema: Union[Schema, Field, Dict[str, Field]] = None,
        semtype: Union[Semantic, str] = None,
    ):
        super().__init__(name)
        self.writeproperty_forwarder = writeproperty_forwarder
        self.readproperty_forwarder = readproperty_forwarder
        self.readonly = readonly
        self.description = description or ""
        self.summary = self.description.partition("\n")[0].strip()
        self.schema = schema

        if isinstance(semtype, Semantic):
            self = semtype(self)
        elif isinstance(semtype, str) or semtype is None:
            self.semtype = semtype
        else:
            raise TypeError("Argument semtype must be a Semantic object or string")

        self._tags = tags
        self._value = None

        self._methodmap = {
            "get": "readproperty",
            "put": "writeproperty",
            "websocket": None,
        }

        if self.readonly:
            self.writeproperty = None

    @property
    def tags(self):
        tags = set(self._tags)
        tags.add("properties")
        return tags

    @property
    def value(self):
        if self.readproperty_forwarder:
            self._value = self.readproperty_forwarder()
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        if self.writeproperty_forwarder:
            self.writeproperty_forwarder(value)

    def readproperty(self):
        return self.value

    def writeproperty(self, value):
        # TODO: Event emitter
        self.value = value
        return self.value

    def dispatch_request(self, *args, **kwargs):
        """

        :param *args: 
        :param **kwargs: 

        """
        method_name = self._find_request_method()
        method = getattr(self, method_name, None)

        # POST and PUT methods can be used to write properties
        # In all other cases, ignore arguments
        if method_name == "writeproperty" and self.schema:
            method = use_args(self.schema)(method)

        # All methods should serialise properties
        if self.schema:
            method = marshal_with(self.schema)(method)

        # Generate basic response
        return self._represent_response(method(*args, **kwargs))


class Action(Interaction):
    def __init__(
        self,
        name: str,
        invokeaction_forwarder: Callable,
        description: str = "",
        tags: List[str] = [],
        safe: bool = False,
        idempotent: bool = False,
        args: Union[Schema, Field, Dict[str, Field]] = None,
        schema: Union[Schema, Field, Dict[str, Field]] = None,
        semtype: Semantic = None,
        wait_for: int = 1,
        default_stop_timeout: int = None,
    ):
        super().__init__(name)
        self.invokeaction_forwarder = invokeaction_forwarder
        self.description = description or ""
        self.summary = self.description.partition("\n")[0].strip()
        self.safe = safe
        self.idempotent = idempotent

        self.args = args
        self.schema = schema

        if isinstance(semtype, Semantic):
            self = semtype(self)
        elif isinstance(semtype, str) or semtype is None:
            self.semtype = semtype
        else:
            raise TypeError("Argument semtype must be a Semantic object or string")

        self._tags = tags

        # Action handling
        self.wait_for = wait_for
        self.default_stop_timeout = default_stop_timeout

        # Action queue
        self._queue_schema = build_action_schema(self.schema, self.args)(many=True)
        self._deque = Deque()  # Action queue
        self._emergency_pool = Pool()

        self._methodmap = {
            "post": "invokeaction",
        }

    @property
    def tags(self):
        tags = set(self._tags)
        tags.add("actions")
        return tags

    def invokeaction(self, *args, **kwargs):
        # TODO: Event emitter
        if self.invokeaction_forwarder:
            return self.invokeaction_forwarder(*args, **kwargs)

    def queue(self):
        """
        Default method for GET requests. 
        Returns the action queue (including already finished actions) for this action
        """

        return self._queue_schema.dump(self._deque)

    def dispatch_request(self, *args, **kwargs):
        """

        :param *args: 
        :param **kwargs: 

        """
        print("Action.dispatch_request")
        method_name = self._find_request_method()
        method = getattr(self, method_name, None)

        # Inject request arguments if an args schema is defined
        if self.args:
            method = use_args(self.args)(method)

        # Marhal response if a response schema is defined
        if self.schema:
            method = marshal_with(self.schema)(method)

        # Try to find a pool on the current LabThing,
        # but fall back to Views emergency pool
        pool = (
            current_labthing().action_pool
            if current_labthing()
            else self._emergency_pool
        )
        # Make a task out of the views `post` method
        task = pool.spawn(method, *args, **kwargs)
        # Optionally override the threads default_stop_timeout
        if self.default_stop_timeout is not None:
            task.default_stop_timeout = self.default_stop_timeout

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
            return self._represent_response((task.output, 200))

        return self._represent_response((ActionSchema().dump(task), 201))
