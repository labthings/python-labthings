import json

import pytest
from flask import Flask

from labthings.labthing import SerializedExceptionHandler


@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


def test_registering_handler(app):
    error_handler = SerializedExceptionHandler()
    error_handler.init_app(app)


def test_http_exception(app):
    from werkzeug.exceptions import NotFound

    error_handler = SerializedExceptionHandler(app)

    # Test a 404 HTTPException
    response = error_handler.std_handler(NotFound())

    response_json = json.dumps(response[0])
    assert (
        response_json
        == '{"code": 404, "message": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.", "name": "NotFound"}'
    )

    assert response[1] == 404


def test_generic_exception(app):
    error_handler = SerializedExceptionHandler(app)

    # Test a 404 HTTPException
    response = error_handler.std_handler(RuntimeError("Exception message"))

    response_json = json.dumps(response[0])
    assert (
        response_json
        == '{"code": 500, "message": "Exception message", "name": "RuntimeError"}'
    )

    assert response[1] == 500


def test_blank_exception(app):
    error_handler = SerializedExceptionHandler(app)

    e = Exception()
    e.message = None

    # Test a 404 HTTPException
    response = error_handler.std_handler(e)

    response_json = json.dumps(response[0])
    assert response_json == '{"code": 500, "message": "None", "name": "Exception"}'

    assert response[1] == 500
