import pytest

import os
import json
import jsonschema
from labthings.server import fields
from labthings.server.spec import td


@pytest.fixture
def thing_description(thing):
    return thing.thing_description


def validate_thing_description(thing_description, app_ctx, schemas_path):
    schema = json.load(open(os.path.join(schemas_path, "w3_wot_td_v1.json"), "r"))
    jsonschema.Draft7Validator.check_schema(schema)

    with app_ctx.test_request_context():
        td_json = thing_description.to_dict()
        assert td_json

    jsonschema.validate(instance=td_json, schema=schema)


def test_find_schema_for_view_readonly():
    class ViewClass:
        def get(self):
            pass

    ViewClass.get.__apispec__ = {"_schema": {200: "schema"}}
    assert td.find_schema_for_view(ViewClass) == "schema"


def test_find_schema_for_view_writeonly_post():
    class ViewClass:
        def post(self):
            pass

    ViewClass.post.__apispec__ = {"_params": "params"}
    assert td.find_schema_for_view(ViewClass) == "params"


def test_find_schema_for_view_writeonly_put():
    class ViewClass:
        def put(self):
            pass

    ViewClass.put.__apispec__ = {"_params": "params"}
    assert td.find_schema_for_view(ViewClass) == "params"


def test_find_schema_for_view_none():
    class ViewClass:
        pass

    assert td.find_schema_for_view(ViewClass) == {}


def test_td_init(thing_description, app_ctx, schemas_path):
    assert thing_description

    validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_add_link(thing_description, view_cls, app_ctx, schemas_path):
    thing_description.add_link(view_cls, "rel")
    assert {
        "rel": "rel",
        "view": view_cls,
        "params": {},
        "kwargs": {},
    } in thing_description._links

    validate_thing_description(thing_description, app_ctx, schemas_path)


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


def test_td_action(app, thing_description, view_cls, app_ctx, schemas_path):
    app.add_url_rule("/", view_func=view_cls.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.action(rules, view_cls)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("actions")
        validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_action_with_schema(app, thing_description, view_cls, app_ctx, schemas_path):
    view_cls.post.__apispec__ = {"_params": {"integer": fields.Int()}}

    app.add_url_rule("/", view_func=view_cls.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.action(rules, view_cls)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("actions")
        assert thing_description.to_dict().get("actions").get("index").get("input") == {
            "type": "object",
            "properties": {"integer": {"type": "integer", "format": "int32"}},
        }
        validate_thing_description(thing_description, app_ctx, schemas_path)
