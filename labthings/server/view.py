from flask.views import MethodView
from flask import request
from werkzeug.wrappers import Response as ResponseBase

from labthings.core.utilities import OrderedDict

from labthings.server.utilities import unpack
from labthings.server.representations import DEFAULT_REPRESENTATIONS


class View(MethodView):
    """
    A LabThing Resource class should make use of functions get(), put(), post(), and delete() 
    corresponding to HTTP methods.

    These functions will allow for automated documentation generation
    """

    methods = ["get", "post", "put", "delete"]
    endpoint = None

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

        # Set the default representations
        # TODO: Inherit from parent LabThing. See original flask_restful implementation
        self.representations = OrderedDict(DEFAULT_REPRESENTATIONS)

    def doc(self):
        docs = {"operations": {}}
        if hasattr(self, "__apispec__"):
            docs.update(self.__apispec__)

        for meth in View.methods:
            if hasattr(self, meth) and hasattr(getattr(self, meth), "__apispec__"):
                docs["operations"][meth] = {}
                docs["operations"][meth] = getattr(self, meth).__apispec__
        return docs

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)

        # If the request method is HEAD and we don't have a handler for it
        # retry with GET.
        if meth is None and request.method == "HEAD":
            meth = getattr(self, "get", None)

        assert meth is not None, "Unimplemented method %r" % request.method

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
