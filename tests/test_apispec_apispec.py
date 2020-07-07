from labthings.apispec import apispec
from labthings.view import View

from labthings import fields


def test_view_to_apispec_operations_no_spec(spec):
    class Index(View):
        """Index docstring"""

        def get(self):
            return "GET"

        def post(self):
            return "POST"

    assert apispec.view_to_apispec_operations(Index, spec) == {
        "get": {
            "description": "Index docstring",
            "summary": "Index docstring",
            "tags": [],
            "responses": {
                200: {"description": "OK", "content": {"application/json": {}}}
            },
        },
        "post": {
            "description": "Index docstring",
            "summary": "Index docstring",
            "tags": [],
            "responses": {
                200: {"description": "OK", "content": {"application/json": {}}}
            },
        },
    }


def test_view_to_apispec_tags(spec):
    class Index(View):
        """Index docstring"""

        tags = set(["tag1", "tag2"])

        def get(self):
            return "GET"

        def post(self):
            return "POST"

    spec_ops = apispec.view_to_apispec_operations(Index, spec)

    assert set(spec_ops["get"]["tags"]) == Index.tags
    assert set(spec_ops["post"]["tags"]) == Index.tags


def test_dict_to_apispec_operations_params(spec):
    class Index(View):
        """Index docstring"""

        args = {"integer": fields.Int()}

        def put(self):
            return "GET"

    assert (apispec.view_to_apispec_operations(Index, spec))["put"]["requestBody"] == {
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

        schema = {"integer": fields.Int()}

        def get(self):
            return "GET"

    assert apispec.view_to_apispec_operations(Index, spec)["get"]["responses"][200] == {
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


def test_rule_to_apispec_path(app, spec):
    class Index(View):
        """Index docstring"""

        def get(self):
            return "GET"

        def post(self):
            return "POST"

    app.add_url_rule("/path", view_func=Index.as_view("index"))
    rule = app.url_map._rules_by_endpoint["index"][0]

    assert apispec.rule_to_apispec_path(rule, Index, spec) == {
        "path": "/path",
        "operations": {
            "get": {
                "description": "Index docstring",
                "summary": "Index docstring",
                "tags": [],
                "responses": {
                    200: {"description": "OK", "content": {"application/json": {}}}
                },
            },
            "post": {
                "description": "Index docstring",
                "summary": "Index docstring",
                "tags": [],
                "responses": {
                    200: {"description": "OK", "content": {"application/json": {}}}
                },
            },
        },
    }


def test_rule_to_apispec_path_params(app, spec):
    class Index(View):
        """Index docstring"""

        def get(self):
            return "GET"

        def post(self):
            return "POST"

    app.add_url_rule("/path/<id>/", view_func=Index.as_view("index"))
    rule = app.url_map._rules_by_endpoint["index"][0]

    assert apispec.rule_to_apispec_path(rule, Index, spec) == {
        "path": "/path/{id}/",
        "operations": {
            "get": {
                "description": "Index docstring",
                "summary": "Index docstring",
                "tags": [],
                "responses": {
                    200: {"description": "OK", "content": {"application/json": {}}}
                },
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
                "description": "Index docstring",
                "summary": "Index docstring",
                "tags": [],
                "responses": {
                    200: {"description": "OK", "content": {"application/json": {}}}
                },
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
    }
