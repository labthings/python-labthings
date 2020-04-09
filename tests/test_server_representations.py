from labthings.server import representations
from flask import Flask, Response
import pytest


@pytest.fixture()
def app(request):

    app = Flask(__name__)

    # pushes an application context manually
    ctx = app.app_context()
    ctx.push()

    # bind the test life with the context through the
    request.addfinalizer(ctx.pop)
    return app


@pytest.fixture()
def debug_app(request):

    app = Flask(__name__)
    app.debug = True

    # pushes an application context manually
    ctx = app.app_context()
    ctx.push()

    # bind the test life with the context through the
    request.addfinalizer(ctx.pop)
    return app


@pytest.fixture()
def app_context(app):
    with app.app_context():
        yield app


@pytest.fixture()
def app_context_debug(debug_app):
    with debug_app.app_context():
        yield debug_app


@pytest.fixture
def labthings_json_encoder():
    return representations.LabThingsJSONEncoder


def test_encoder_default_exception(labthings_json_encoder):
    with pytest.raises(TypeError):
        labthings_json_encoder().default("")


def test_encode_json(labthings_json_encoder):
    data = {
        "a": "String",
        "b": 5,
        "c": [10, 20, 30, 40, 50],
        "d": {"a": "String", "b": 5, "c": [10, 20, 30, 40, 50]},
    }
    assert (
        representations.encode_json(data, encoder=labthings_json_encoder)
        == '{"a": "String", "b": 5, "c": [10, 20, 30, 40, 50], "d": {"a": "String", "b": 5, "c": [10, 20, 30, 40, 50]}}\n'
    )


def test_output_json(app_context):
    data = {
        "a": "String",
        "b": 5,
        "c": [10, 20, 30, 40, 50],
        "d": {"a": "String", "b": 5, "c": [10, 20, 30, 40, 50]},
    }

    with app_context.test_request_context():
        response = representations.output_json(data, 200)
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert (
            response.data
            == b'{"a": "String", "b": 5, "c": [10, 20, 30, 40, 50], "d": {"a": "String", "b": 5, "c": [10, 20, 30, 40, 50]}}\n'
        )


def test_pretty_output_json(app_context_debug):
    data = {
        "a": "String",
        "b": 5,
        "c": [10, 20, 30, 40, 50],
        "d": {"a": "String", "b": 5, "c": [10, 20, 30, 40, 50]},
    }

    with app_context_debug.test_request_context():
        response = representations.output_json(data, 200)
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert (
            response.data
            == b'{\n    "a": "String",\n    "b": 5,\n    "c": [\n        10,\n        20,\n        30,\n        40,\n        50\n    ],\n    "d": {\n        "a": "String",\n        "b": 5,\n        "c": [\n            10,\n            20,\n            30,\n            40,\n            50\n        ]\n    }\n}\n'
        )