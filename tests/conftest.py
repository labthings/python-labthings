import pytest
import os
from flask import Flask
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from labthings.server.labthing import LabThing
from labthings.server.view import View

from flask.testing import FlaskClient


class JsonClient(FlaskClient):
    def open(self, *args, **kwargs):
        kwargs.setdefault(
            "headers",
            {"Content-Type": "application/json", "Accept": "application/json"},
        )
        kwargs.setdefault("content_type", "application/json")
        return super().open(*args, **kwargs)


@pytest.fixture
def view_cls():
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
    thing = LabThing(app)
    with app.app_context():
        return thing


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


class FakeWebsocket:
    def __init__(self, message: str, recieve_once=True):
        self.message = message
        self.response = None
        self.closed = False
        self.recieve_once = recieve_once

    def receive(self):
        # Get message
        message_to_send = self.message
        # If only sending a message to the server once
        if self.recieve_once:
            # Clear our message
            self.message = None
        return message_to_send

    def send(self, response):
        self.response = response
        self.closed = True
        return response


@pytest.fixture
def fake_websocket():
    """
    Return a fake websocket client 
    that sends a given message, waits for a response, then closes
    """

    def _foo(msg, recieve_once=True):
        return FakeWebsocket(msg, recieve_once=recieve_once)

    return _foo
