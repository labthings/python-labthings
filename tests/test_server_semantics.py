import pytest

from labthings.server.view import View
from labthings.server import semantics


@pytest.fixture
def thing_description(thing):
    return thing.thing_description


def test_moz_BooleanProperty(helpers, app, thing_description, app_ctx, schemas_path):
    @semantics.moz.BooleanProperty()
    class Index(View):
        def get(self):
            return "GET"

    app.add_url_rule("/", view_func=Index.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.property(rules, Index)

    with app_ctx.test_request_context():
        assert (
            thing_description.to_dict()["properties"]["index"]["@type"]
            == "BooleanProperty"
        )
        assert thing_description.to_dict()["properties"]["index"]["type"] == "boolean"
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_moz_LevelProperty(helpers, app, thing_description, app_ctx, schemas_path):
    @semantics.moz.LevelProperty(0, 100)
    class Index(View):
        def get(self):
            return "GET"

    app.add_url_rule("/", view_func=Index.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.property(rules, Index)

    with app_ctx.test_request_context():
        assert (
            thing_description.to_dict()["properties"]["index"]["@type"]
            == "LevelProperty"
        )
        assert thing_description.to_dict()["properties"]["index"]["type"] == "integer"
        assert thing_description.to_dict()["properties"]["index"]["minimum"] == 0
        assert thing_description.to_dict()["properties"]["index"]["maximum"] == 100
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_moz_BrightnessProperty(helpers, app, thing_description, app_ctx, schemas_path):
    @semantics.moz.BrightnessProperty()
    class Index(View):
        def get(self):
            return "GET"

    app.add_url_rule("/", view_func=Index.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.property(rules, Index)

    with app_ctx.test_request_context():
        assert (
            thing_description.to_dict()["properties"]["index"]["@type"]
            == "BrightnessProperty"
        )
        assert thing_description.to_dict()["properties"]["index"]["type"] == "integer"
        assert thing_description.to_dict()["properties"]["index"]["minimum"] == 0
        assert thing_description.to_dict()["properties"]["index"]["maximum"] == 100
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_moz_OnOffProperty(helpers, app, thing_description, app_ctx, schemas_path):
    @semantics.moz.OnOffProperty()
    class Index(View):
        def get(self):
            return "GET"

    app.add_url_rule("/", view_func=Index.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.property(rules, Index)

    with app_ctx.test_request_context():
        assert (
            thing_description.to_dict()["properties"]["index"]["@type"]
            == "OnOffProperty"
        )
        assert thing_description.to_dict()["properties"]["index"]["type"] == "boolean"
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)
