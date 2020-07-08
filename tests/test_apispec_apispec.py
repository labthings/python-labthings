from labthings.apispec import apispec
from labthings.view import View, PropertyView

from labthings import fields


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
            "post": {
                "description": "Index docstring",
                "summary": "Index docstring",
                "tags": [],
            },
            "get": {
                "description": "Index docstring",
                "summary": "Index docstring",
                "tags": [],
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
            "post": {
                "description": "Index docstring",
                "summary": "Index docstring",
                "tags": [],
                "parameters": [
                    {
                        "in": "path",
                        "name": "id",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
            },
            "get": {
                "description": "Index docstring",
                "summary": "Index docstring",
                "tags": [],
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
