from labthings.server.spec import apispec
from labthings.server.spec.utilities import compile_view_spec
from labthings.server.view import View

from labthings.server import fields


def test_dict_to_apispec_operations_no_spec(spec):
    class Index(View):
        def get(self):
            return "GET"

        def post(self):
            return "POST"

    spec_dict = compile_view_spec(Index)

    assert apispec.dict_to_apispec_operations(spec_dict["_operations"], spec) == {
        "get": {
            "responses": {200: {"description": "OK"}},
            "description": "",
            "summary": "",
            "tags": set(),
        },
        "post": {
            "responses": {200: {"description": "OK"}},
            "description": "",
            "summary": "",
            "tags": set(),
        },
    }


def test_dict_to_apispec_operations_params(spec):
    class Index(View):
        def get(self):
            return "GET"

    spec_dict = compile_view_spec(Index)
    spec_dict["_operations"]["get"]["_params"] = {"integer": fields.Int()}

    assert (apispec.dict_to_apispec_operations(spec_dict["_operations"], spec))["get"][
        "requestBody"
    ] == {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"integer": {"type": "integer", "format": "int32"}},
                }
            }
        }
    }


def test_dict_to_apispec_operations_schema(spec):
    class Index(View):
        def get(self):
            return "GET"

    spec_dict = compile_view_spec(Index)
    spec_dict["_operations"]["get"]["_schema"] = {200: {"integer": fields.Int()}}

    assert (apispec.dict_to_apispec_operations(spec_dict["_operations"], spec))["get"][
        "responses"
    ][200] == {
        "description": "OK",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"integer": {"type": "integer", "format": "int32"}},
                }
            }
        },
    }


def test_method_to_apispec_operation_extra_fields(spec):
    class Index(View):
        def get(self):
            return "GET"

    spec_dict = compile_view_spec(Index)
    spec_dict["_operations"]["get"]["summary"] = "A summary"

    assert (apispec.dict_to_apispec_operations(spec_dict["_operations"], spec))["get"][
        "summary"
    ] == "A summary"


def test_rule_to_apispec_path(app, spec):
    class Index(View):
        def get(self):
            return "GET"

        def post(self):
            return "POST"

    app.add_url_rule("/path", view_func=Index.as_view("index"))
    rule = app.url_map._rules_by_endpoint["index"][0]

    spec_dict = compile_view_spec(Index)

    assert apispec.rule_to_apispec_path(rule, spec_dict, spec) == {
        "path": "/path",
        "operations": {
            "get": {
                "responses": {200: {"description": "OK"}},
                "description": "",
                "summary": "",
                "tags": set(),
            },
            "post": {
                "responses": {200: {"description": "OK"}},
                "description": "",
                "summary": "",
                "tags": set(),
            },
        },
        "description": "",
        "summary": "",
        "tags": set(),
    }


def test_rule_to_apispec_path_params(app, spec):
    class Index(View):
        def get(self):
            return "GET"

        def post(self):
            return "POST"

    app.add_url_rule("/path/<id>/", view_func=Index.as_view("index"))
    rule = app.url_map._rules_by_endpoint["index"][0]

    spec_dict = compile_view_spec(Index)

    assert apispec.rule_to_apispec_path(rule, spec_dict, spec) == {
        "path": "/path/{id}/",
        "operations": {
            "get": {
                "responses": {200: {"description": "OK"}},
                "description": "",
                "summary": "",
                "tags": set(),
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
                "responses": {200: {"description": "OK"}},
                "description": "",
                "summary": "",
                "tags": set(),
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
        "description": "",
        "summary": "",
        "tags": set(),
    }
