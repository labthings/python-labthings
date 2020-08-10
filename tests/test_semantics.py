import pytest

from labthings.views import PropertyView, op
from labthings import semantics


@pytest.fixture
def thing_description(thing):
    return thing.thing_description


def test_moz_BooleanProperty(helpers, app, thing_description, app_ctx, schemas_path):
    @semantics.moz.BooleanProperty()
    class Index(PropertyView):
        @op.readproperty
        def get(self):
            return "GET"

    interaction = Index.as_interaction()
    app.add_url_rule("/", view_func=Index.as_view("index"), endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]

    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert (
            thing_description.to_dict()["properties"][interaction.name]["@type"]
            == "BooleanProperty"
        )
        assert (
            thing_description.to_dict()["properties"][interaction.name]["type"]
            == "boolean"
        )
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_moz_LevelProperty(helpers, app, thing_description, app_ctx, schemas_path):
    @semantics.moz.LevelProperty(0, 100)
    class Index(PropertyView):
        @op.readproperty
        def get(self):
            return "GET"

    interaction = Index.as_interaction()
    app.add_url_rule("/", view_func=Index.as_view("index"), endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]

    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert (
            thing_description.to_dict()["properties"][interaction.name]["@type"]
            == "LevelProperty"
        )
        assert (
            thing_description.to_dict()["properties"][interaction.name]["type"]
            == "number"
        )
        assert (
            thing_description.to_dict()["properties"][interaction.name]["format"]
            == "integer"
        )
        assert (
            thing_description.to_dict()["properties"][interaction.name]["minimum"] == 0
        )
        assert (
            thing_description.to_dict()["properties"][interaction.name]["maximum"]
            == 100
        )
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_moz_BrightnessProperty(helpers, app, thing_description, app_ctx, schemas_path):
    @semantics.moz.BrightnessProperty()
    class Index(PropertyView):
        @op.readproperty
        def get(self):
            return "GET"

    interaction = Index.as_interaction()
    app.add_url_rule("/", view_func=Index.as_view("index"), endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]

    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert (
            thing_description.to_dict()["properties"][interaction.name]["@type"]
            == "BrightnessProperty"
        )
        assert (
            thing_description.to_dict()["properties"][interaction.name]["type"]
            == "number"
        )
        assert (
            thing_description.to_dict()["properties"][interaction.name]["format"]
            == "integer"
        )
        assert (
            thing_description.to_dict()["properties"][interaction.name]["minimum"] == 0
        )
        assert (
            thing_description.to_dict()["properties"][interaction.name]["maximum"]
            == 100
        )
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_moz_OnOffProperty(helpers, app, thing_description, app_ctx, schemas_path):
    @semantics.moz.OnOffProperty()
    class Index(PropertyView):
        @op.readproperty
        def get(self):
            return "GET"

    interaction = Index.as_interaction()
    app.add_url_rule("/", view_func=Index.as_view("index"), endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]

    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert (
            thing_description.to_dict()["properties"][interaction.name]["@type"]
            == "OnOffProperty"
        )
        assert (
            thing_description.to_dict()["properties"][interaction.name]["type"]
            == "boolean"
        )
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)
