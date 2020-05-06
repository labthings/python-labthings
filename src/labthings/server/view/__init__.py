from flask.views import MethodView
from flask import request
from werkzeug.wrappers import Response as ResponseBase

from collections import OrderedDict

from ..utilities import unpack
from ..representations import DEFAULT_REPRESENTATIONS
from ..find import current_labthing
from ..event import PropertyStatusEvent, ActionStatusEvent
from ..schema import ActionSchema

from labthings.core.tasks import taskify

from gevent.timeout import Timeout


class View(MethodView):
    """
    A LabThing Resource class should make use of functions
    get(), put(), post(), and delete(), corresponding to HTTP methods.

    These functions will allow for automated documentation generation
    """

    endpoint = None
    __apispec__ = {}

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

        # Set the default representations
        # TODO: Inherit from parent LabThing. See original flask_restful implementation
        self.representations = OrderedDict(DEFAULT_REPRESENTATIONS)

    def get_value(self):
        get_method = getattr(self, "get", None)  # Look for this views GET method
        if get_method is None:
            return None
        if not callable(get_method):
            raise TypeError("Attribute 'get' of View must be a callable")
        response = get_method()  # pylint: disable=not-callable
        if isinstance(response, ResponseBase):  # Pluck useful data out of HTTP response
            return response.json if response.json else response.data.decode()
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

        # Generate basic response
        return self.represent_response(meth(*args, **kwargs))

    def represent_response(self, response):
        """
        Take the return balue of a function and build a representation response
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

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)

        # Let base View handle non-POST requests
        if request.method != "POST":
            return View.dispatch_request(self, *args, **kwargs)

        task = taskify(meth)(*args, **kwargs)

        # Wait up to 2 second for the action to complete
        try:
            task.get(block=True, timeout=1)
        except Timeout:
            pass
        return self.represent_response(ActionSchema().dump(task))


class PropertyView(View):
    __apispec__ = {"tags": {"properties"}}

    def dispatch_request(self, *args, **kwargs):
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
