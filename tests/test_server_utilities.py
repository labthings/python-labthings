import pytest

from labthings.server import utilities
from labthings.server.view import View


def test_http_status_message():
    assert utilities.http_status_message(404) == "Not Found"


def test_http_status_missing():
    # Totally invalid HTTP code
    assert utilities.http_status_message(0) == ""


def test_description_from_view(app):
    class Index(View):
        """Class summary"""

        @staticmethod
        def get():
            """GET summary"""
            return "GET"

        @staticmethod
        def post():
            """POST summary"""
            return "POST"

    assert utilities.description_from_view(Index) == {
        "methods": ["GET", "POST"],
        "description": "Class summary",
    }


def test_description_from_view_summary_from_method(app):
    class Index(View):
        @staticmethod
        def get():
            """GET summary"""
            return "GET"

        @staticmethod
        def post():
            """POST summary"""
            return "POST"

    assert utilities.description_from_view(Index) == {
        "methods": ["GET", "POST"],
        "description": "GET summary",
    }


def test_view_class_from_endpoint(app):
    class Index(View):
        @staticmethod
        def get():
            return "GET"

        @staticmethod
        def post():
            return "POST"

    app.add_url_rule("/", view_func=Index.as_view("index"))
    assert utilities.view_class_from_endpoint("index") == Index


def test_unpack_data():
    assert utilities.unpack("value") == ("value", 200, {})


def test_unpack_data_tuple():
    assert utilities.unpack(("value",)) == (("value",), 200, {})


def test_unpack_data_code():
    assert utilities.unpack(("value", 201)) == ("value", 201, {})


def test_unpack_data_code_headers():
    assert utilities.unpack(("value", 201, {"header": "header_value"})) == (
        "value",
        201,
        {"header": "header_value"},
    )


def test_clean_url_string():
    assert utilities.clean_url_string(None) == "/"
    assert utilities.clean_url_string("path") == "/path"
    assert utilities.clean_url_string("/path") == "/path"
    assert utilities.clean_url_string("//path") == "//path"
