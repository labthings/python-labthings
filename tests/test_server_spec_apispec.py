import pytest

from labthings.server.spec import apispec
from labthings.server.view import View

from labthings.server import fields


def test_method_to_apispec_operation_no_spec(spec):
    class Index(View):
        @staticmethod
        def get():
            return "GET"

        @staticmethod
        def post():
            return "POST"

    assert apispec.method_to_apispec_operation(Index.get, spec) == {
        "responses": {200: {"description": "OK"}}
    }


def test_method_to_apispec_operation_params(spec):
    class Index(View):
        @staticmethod
        def get():
            return "GET"

    Index.get.__apispec__ = {"_params": {"integer": fields.Int()}}

    assert apispec.method_to_apispec_operation(Index.get, spec) == {
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "integer": {"type": "integer", "format": "int32"}
                        },
                    }
                }
            }
        },
        "responses": {200: {"description": "OK"}},
    }


def test_method_to_apispec_operation_schema(spec):
    class Index(View):
        @staticmethod
        def get():
            return "GET"

    Index.get.__apispec__ = {"_schema": {200: {"integer": fields.Int()}}}

    assert apispec.method_to_apispec_operation(Index.get, spec) == {
        "responses": {
            200: {
                "description": "OK",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "integer": {"type": "integer", "format": "int32"}
                            },
                        }
                    }
                },
            }
        }
    }


def test_method_to_apispec_operation_extra_fields(spec):
    class Index(View):
        @staticmethod
        def get():
            return "GET"

    Index.get.__apispec__ = {"summary": "A summary"}

    assert apispec.method_to_apispec_operation(Index.get, spec) == {
        "summary": "A summary",
        "responses": {200: {"description": "OK"}},
    }


def test_view_to_apispec_operations(spec):
    class Index(View):
        @staticmethod
        def get():
            return "GET"

        @staticmethod
        def post():
            return "POST"

    assert apispec.view_to_apispec_operations(Index, spec) == {
        "post": {
            "description": None,
            "summary": None,
            "tags": set(),
            "responses": {200: {"description": "OK"}},
        },
        "get": {
            "description": None,
            "summary": None,
            "tags": set(),
            "responses": {200: {"description": "OK"}},
        },
    }


def test_rule_to_apispec_path(app, spec):
    class Index(View):
        @staticmethod
        def get():
            return "GET"

        @staticmethod
        def post():
            return "POST"

    app.add_url_rule("/path", view_func=Index.as_view("index"))
    rule = app.url_map._rules_by_endpoint["index"][0]
    assert apispec.rule_to_apispec_path(rule, Index, spec) == {
        "path": "/path",
        "operations": {
            "get": {
                "description": None,
                "summary": None,
                "tags": set(),
                "responses": {200: {"description": "OK"}},
            },
            "post": {
                "description": None,
                "summary": None,
                "tags": set(),
                "responses": {200: {"description": "OK"}},
            },
        },
        "description": None,
        "summary": None,
        "tags": set(),
    }


def test_rule_to_apispec_path_params(app, spec):
    class Index(View):
        @staticmethod
        def get():
            return "GET"

        @staticmethod
        def post():
            return "POST"

    app.add_url_rule("/path/<id>/", view_func=Index.as_view("index"))
    rule = app.url_map._rules_by_endpoint["index"][0]
    assert apispec.rule_to_apispec_path(rule, Index, spec) == {
        "path": "/path/{id}/",
        "operations": {
            "get": {
                "description": None,
                "summary": None,
                "tags": set(),
                "responses": {200: {"description": "OK"}},
                "parameters": [
                    {
                        "in": "path",
                        "name": "id",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
            },
            "post": {
                "description": None,
                "summary": None,
                "tags": set(),
                "responses": {200: {"description": "OK"}},
                "parameters": [
                    {
                        "in": "path",
                        "name": "id",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
            },
        },
        "description": None,
        "summary": None,
        "tags": set(),
    }


def test_rule_to_apispec_path_extra_class_params(app, spec):
    class Index(View):
        @staticmethod
        def get():
            return "GET"

    Index.__apispec__ = {"summary": "A class summary"}

    app.add_url_rule("/path", view_func=Index.as_view("index"))
    rule = app.url_map._rules_by_endpoint["index"][0]

    assert apispec.rule_to_apispec_path(rule, Index, spec) == {
        "path": "/path",
        "operations": {
            "get": {
                "description": None,
                "summary": "A class summary",
                "tags": set(),
                "responses": {200: {"description": "OK"}},
            }
        },
        "description": None,
        "summary": "A class summary",
        "tags": set(),
    }


def test_rule_to_apispec_path_extra_method_params(app, spec):
    class Index(View):
        @staticmethod
        def get():
            return "GET"

    Index.get.__apispec__ = {"summary": "A GET summary"}

    app.add_url_rule("/path", view_func=Index.as_view("index"))
    rule = app.url_map._rules_by_endpoint["index"][0]

    assert apispec.rule_to_apispec_path(rule, Index, spec) == {
        "path": "/path",
        "operations": {
            "get": {
                "description": None,
                "summary": "A GET summary",
                "tags": set(),
                "responses": {200: {"description": "OK"}},
            }
        },
        "description": None,
        "summary": None,
        "tags": set(),
    }
