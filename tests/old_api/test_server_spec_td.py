import pytest

from labthings.server import fields
from labthings.server.view import View
from labthings.server.spec import td


@pytest.fixture
def thing_description(thing):
    return thing.thing_description


def test_td_init(helpers, thing_description, app_ctx, schemas_path):
    assert thing_description
    helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_add_link(helpers, thing_description, view_cls, app_ctx, schemas_path):
    thing_description.add_link(view_cls, "rel")
    assert {
        "rel": "rel",
        "view": view_cls,
        "params": {},
        "kwargs": {},
    } in thing_description._links

    helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_add_link_options(thing_description, view_cls):
    thing_description.add_link(
        view_cls, "rel", kwargs={"kwarg": "kvalue"}, params={"param": "pvalue"}
    )
    assert {
        "rel": "rel",
        "view": view_cls,
        "params": {"param": "pvalue"},
        "kwargs": {"kwarg": "kvalue"},
    } in thing_description._links


def test_td_links(thing_description, app_ctx, view_cls):
    thing_description.add_link(
        view_cls, "rel", kwargs={"kwarg": "kvalue"}, params={"param": "pvalue"}
    )

    with app_ctx.test_request_context():
        assert {"rel": "rel", "href": "", "kwarg": "kvalue"} in (
            thing_description.links
        )


def test_td_action(helpers, app, thing_description, view_cls, app_ctx, schemas_path):
    app.add_url_rule("/", view_func=view_cls.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.action(rules, view_cls)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("actions")
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_action_with_schema(
    helpers, app, thing_description, view_cls, app_ctx, schemas_path
):
    view_cls.args = {"integer": fields.Int()}
    view_cls.semtype = "ToggleAction"

    app.add_url_rule("/", view_func=view_cls.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.action(rules, view_cls)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("actions")

        assert thing_description.to_dict().get("actions").get("index") == {
            "title": "ViewClass",
            "description": "",
            "links": [{"href": "/"}],
            "safe": False,
            "idempotent": False,
            "forms": [
                {
                    "op": ["invokeaction"],
                    "htv:methodName": "POST",
                    "href": "/",
                    "contentType": "application/json",
                }
            ],
            "input": {
                "type": "object",
                "properties": {"integer": {"type": "number", "format": "integer"}},
            },
            "@type": "ToggleAction",
        }
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_property(helpers, app, thing_description, app_ctx, schemas_path):
    class Index(View):
        def get(self):
            return "GET"

    app.add_url_rule("/", view_func=Index.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.property(rules, Index)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("properties")
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_property_with_schema(
    helpers, app, thing_description, app_ctx, schemas_path
):
    class Index(View):
        def get(self):
            return "GET"

    Index.schema = fields.Int(required=True)

    app.add_url_rule("/", view_func=Index.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.property(rules, Index)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("properties")
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_property_with_url_param(
    helpers, app, thing_description, app_ctx, schemas_path
):
    class Index(View):
        def get(self):
            return "GET"

    app.add_url_rule("/path/<int:id>/", view_func=Index.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.property(rules, Index)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("properties")
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_property_write_only(helpers, app, thing_description, app_ctx, schemas_path):
    class Index(View):
        def put(self):
            return "PUT"

    Index.schema = fields.Int()

    app.add_url_rule("/", view_func=Index.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.property(rules, Index)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("properties")
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)
