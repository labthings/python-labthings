from flask.views import MethodView
from flask import request
from werkzeug.wrappers import Response as ResponseBase
from werkzeug.exceptions import MethodNotAllowed

from collections import OrderedDict

from labthings.server.utilities import unpack
from labthings.server.representations import DEFAULT_REPRESENTATIONS


class View(MethodView):
    """
    A LabThing Resource class should make use of functions
    get(), put(), post(), and delete(), corresponding to HTTP methods.

    These functions will allow for automated documentation generation
    """

    methods = ["get", "post", "put", "delete"]
    endpoint = None

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

        # Set the default representations
        # TODO: Inherit from parent LabThing. See original flask_restful implementation
        self.representations = OrderedDict(DEFAULT_REPRESENTATIONS)

    def get_value(self):
        get_method = getattr(self, "get", None)  # Look for this views GET method
        if callable(get_method):  # Check it's callable
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

        if meth is None:
            raise MethodNotAllowed(f"Unimplemented method {request.method}")

        # Generate basic response
        resp = meth(*args, **kwargs)

        if isinstance(resp, ResponseBase):  # There may be a better way to test
            return resp

        representations = self.representations or OrderedDict()

        # noinspection PyUnresolvedReferences
        mediatype = request.accept_mimetypes.best_match(representations, default=None)
        if mediatype in representations:
            data, code, headers = unpack(resp)
            resp = representations[mediatype](data, code, headers)
            resp.headers["Content-Type"] = mediatype
            return resp

        return resp
