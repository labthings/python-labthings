import json
import os

import jsonschema
import pytest
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask
from flask.testing import FlaskClient
from flask.views import MethodView
from werkzeug.test import EnvironBuilder

from labthings import LabThing
from labthings.actions import Pool
from labthings.json import encode_json
from labthings.views import View, ActionView, PropertyView


class Helpers:
    @staticmethod
    def validate_thing_description(thing_description, app_ctx, schemas_path):
        schema = json.load(open(os.path.join(schemas_path, "w3c_td_schema.json"), "r"))
        jsonschema.Draft7Validator.check_schema(schema)

        # Build a TD dictionary
        with app_ctx.test_request_context():
            td_dict = thing_description.to_dict()

        # Allow our LabThingsJSONEncoder to encode the RD
        td_json = encode_json(td_dict)
        # Decode the JSON back into a primitive dictionary
        td_json_dict = json.loads(td_json)
        # Validate
        jsonschema.validate(instance=td_json_dict, schema=schema)


@pytest.fixture
def helpers():
    return Helpers


class FakeWebsocket:
    def __init__(self, message: str, recieve_once=True, close_after=None):
        self.message = message
        self.responses = []
        self.closed = False
        self.recieve_once = recieve_once

        self.close_after = close_after or []

        # I mean screw whoever is responsible for this having to be a thing...
        self.receive = self.recieve

    def recieve(self):
        # Get message
        message_to_send = self.message
        # If only sending a message to the server once
        if self.recieve_once:
            # Clear our message
            self.message = None
        return message_to_send

    @property
    def response(self):
        if len(self.responses) >= 1:
            return self.responses[-1]
        else:
            return None

    def send(self, response):
        self.responses.append(response)
        # Close WS after getting the pre-defined unit test response
        if response in self.close_after:
            self.closed = True
        return response


class JsonClient(FlaskClient):
    def open(self, *args, **kwargs):
        kwargs.setdefault(
            "headers",
            {"Content-Type": "application/json", "Accept": "application/json"},
        )
        kwargs.setdefault("content_type", "application/json")
        return super().open(*args, **kwargs)


class SocketClient(FlaskClient):
    def __init__(self, app, response_wrapper, *args, **kwargs):
        super().__init__(app, response_wrapper, *args, **kwargs)
        self.app = app
        self.response_wrapper = response_wrapper
        self.socket = FakeWebsocket(message=None)
        self.environ_base = {
            "HTTP_UPGRADE": "websocket",
            "wsgi.websocket": self.socket,
        }

    def connect(self, *args, message=None, **kwargs):
        kwargs.setdefault("environ_overrides", {})[
            "flask._preserve_context"
        ] = self.preserve_context
        kwargs.setdefault("environ_base", self.environ_base)
        builder = EnvironBuilder(*args, **kwargs)

        try:
            environ = builder.get_environ()
        finally:
            builder.close()

        self.socket.message = message

        with self.app.app_context():
            run_wsgi_app(self.app, environ)

        # Once the connection has been closed, return responses
        return self.socket.responses


def run_wsgi_app(app, environ, buffered=False):
    response = []
    buffer = []

    def start_response(status, headers, exc_info=None):
        if exc_info:
            try:
                raise exc_info[1].with_traceback(exc_info[2])
            finally:
                exc_info = None
        response[:] = [status, headers]
        return buffer.append

    # Return value from the wsgi_app call
    # In the case of our SocketMiddleware, will return []
    app_rv = app(environ, start_response)
    return app_rv


@pytest.fixture
def empty_view_cls():
    class EmptyViewClass(View):
        def get(self):
            pass

        def post(self):
            pass

        def put(self):
            pass

        def delete(self):
            pass

    return EmptyViewClass


@pytest.fixture
def flask_view_cls():
    class ViewClass(MethodView):
        def get(self):
            return "GET"

        def post(self):
            return "POST"

        def put(self):
            return "PUT"

        def delete(self):
            return "DELETE"

    return ViewClass


@pytest.fixture
def view_cls():
    class ViewClass(View):
        def get(self):
            return "GET"

        def post(self):
            return "POST"

        def put(self):
            return "PUT"

        def delete(self):
            return "DELETE"

    return ViewClass


@pytest.fixture
def action_view_cls():
    class ActionViewClass(ActionView):
        def post(self):
            return "POST"

    return ActionViewClass


@pytest.fixture
def property_view_cls():
    class PropertyViewClass(PropertyView):
        def get(self):
            return "GET"

        def put(self):
            return "PUT"

    return PropertyViewClass


@pytest.fixture
def spec():
    return APISpec(
        title="Python-LabThings PyTest",
        version="1.0.0",
        openapi_version="3.0.2",
        plugins=[MarshmallowPlugin()],
    )


@pytest.fixture()
def app(request):

    app = Flask(__name__)
    app.config["TESTING"] = True

    # pushes an application context manually
    ctx = app.app_context()
    ctx.push()

    # bind the test life with the context through the
    request.addfinalizer(ctx.pop)
    return app


@pytest.fixture
def thing(app):
    thing = LabThing(app, external_links=False)
    with app.app_context():
        return thing


@pytest.fixture()
def thing_ctx(thing):
    with thing.app.app_context():
        yield thing.app


@pytest.fixture()
def debug_app(request):

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.debug = True

    # pushes an application context manually
    ctx = app.app_context()
    ctx.push()

    # bind the test life with the context through the
    request.addfinalizer(ctx.pop)
    return app


@pytest.fixture()
def app_ctx(app):
    with app.app_context():
        yield app


@pytest.fixture()
def app_ctx_debug(debug_app):
    with debug_app.app_context():
        yield debug_app


@pytest.fixture
def req_ctx(app):
    with app.test_request_context() as ctx:
        yield ctx


@pytest.fixture
def client(app):
    app.test_client_class = JsonClient
    return app.test_client()


@pytest.fixture
def debug_client(debug_app):
    debug_app.test_client_class = JsonClient
    return debug_app.test_client()


@pytest.fixture
def text_client(app):
    return app.test_client()


@pytest.fixture
def ws_client(app):
    app.test_client_class = SocketClient
    return app.test_client()


@pytest.fixture
def thing_client(thing):
    thing.app.test_client_class = JsonClient
    return thing.app.test_client()


@pytest.fixture
def static_path(app):
    return os.path.join(os.path.dirname(__file__), "static")


@pytest.fixture
def schemas_path(app):
    return os.path.join(os.path.dirname(__file__), "schemas")


@pytest.fixture
def extensions_path(app):
    return os.path.join(os.path.dirname(__file__), "extensions")


@pytest.fixture
def fake_websocket():
    """
    Return a fake websocket client 
    that sends a given message, waits for a response, then closes
    """

    def _foo(*args, **kwargs):
        return FakeWebsocket(*args, **kwargs)

    return _foo


@pytest.fixture
def task_pool():
    """
    Return a task pool
    """

    return Pool()
