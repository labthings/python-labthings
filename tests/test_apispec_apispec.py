from labthings.apispec import apispec
from labthings.views import View, PropertyView

from labthings import fields


def removed_test_rule_to_apispec_path(app, spec):
    class Index(View):
        """Index docstring"""

        def get(self):
            return "GET"

        def post(self):
            return "POST"

    app.add_url_rule("/path", view_func=Index.as_view("index"))
    rule = app.url_map._rules_by_endpoint["index"][0]

    assert apispec.rule_to_apispec_path(rule, Index, spec)["path"] == "/path"
    for method in ("get", "post"):
        assert method in apispec.rule_to_apispec_path(rule, Index, spec)["operations"]


def removed_test_rule_to_apispec_path_params(app, spec):
    class Index(View):
        """Index docstring"""

        def get(self):
            return "GET"

        def post(self):
            return "POST"

    app.add_url_rule("/path/<id>/", view_func=Index.as_view("index"))
    rule = app.url_map._rules_by_endpoint["index"][0]

    ops = apispec.rule_to_apispec_path(rule, Index, spec)["operations"]
    for method in ("get", "post"):
        assert ops[method]["parameters"] == [
            {
                "in": "path",
                "name": "id",
                "required": True,
                "schema": {"type": "string"},
            }
        ]
