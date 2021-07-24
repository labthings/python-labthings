import json
import os

import jsonschema
import pytest
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask, abort
from flask.testing import FlaskClient
from flask.views import MethodView
from marshmallow import validate

from labthings import LabThing, fields
from labthings.actions import Pool
from labthings.json import encode_json
from labthings.views import ActionView, PropertyView, View


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


class JsonClient(FlaskClient):
    def open(self, *args, **kwargs):
        kwargs.setdefault(
            "headers",
            {"Content-Type": "application/json", "Accept": "application/json"},
        )
        kwargs.setdefault("content_type", "application/json")
        return super().open(*args, **kwargs)


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


@pytest.fixture
def thing_with_some_views(thing):
    class TestAction(ActionView):
        args = {"n": fields.Integer()}

        def post(self):
            return "POST"

    thing.add_view(TestAction, "/TestAction")

    class TestProperty(PropertyView):
        schema = {"count": fields.Integer()}

        def get(self):
            return 1

        def post(self, args):
            pass

    thing.add_view(TestProperty, "/TestProperty")

    class TestFieldProperty(PropertyView):
        schema = fields.String(validate=validate.OneOf(["one", "two"]))

        def get(self):
            return "one"

        def post(self, args):
            pass

    thing.add_view(TestFieldProperty, "/TestFieldProperty")
    
    class FailAction(ActionView):
        wait_for = 1.0
        def post(self):
            raise Exception("This action is meant to fail with an Exception")
    
    thing.add_view(FailAction, "/FailAction")

    class AbortAction(ActionView):
        wait_for = 1.0
        def post(self):
            abort(418, "I'm a teapot! This action should abort with an HTTP code 418")
    
    thing.add_view(AbortAction, "/AbortAction")

    class ActionWithValidation(ActionView):
        wait_for = 1.0
        args = {"test_arg": fields.String(validate=validate.OneOf(["one", "two"]))}
        def post(self):
            return True
    thing.add_view(ActionWithValidation, "/ActionWithValidation")

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
def debug_client(debug_app):
    debug_app.test_client_class = JsonClient
    return debug_app.test_client()


@pytest.fixture
def text_client(app):
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
def task_pool():
    """
    Return a task pool
    """

    return Pool()
