import pytest

from labthings.views import PropertyView, op


@pytest.fixture
def thing_description(thing):
    return thing.thing_description


def test_op_readproperty(helpers, app, thing_description, app_ctx, schemas_path):
    class Index(PropertyView):
        @op.readproperty
        def get(self):
            return "GET"

    interaction = Index.as_interaction()
    app.add_url_rule("/", view_func=Index.as_view("index"), endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]

    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert interaction.name in thing_description.to_dict()["properties"]
        assert (
            thing_description.to_dict()["properties"][interaction.name]["forms"][0][
                "op"
            ]
            == "readproperty"
        )

        assert (
            thing_description.to_dict()["properties"][interaction.name]["forms"][0][
                "htv:methodName"
            ]
            == "GET"
        )
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_op_writeproperty(helpers, app, thing_description, app_ctx, schemas_path):
    class Index(PropertyView):
        @op.writeproperty
        def put(self):
            return "PUT"

    interaction = Index.as_interaction()
    app.add_url_rule("/", view_func=Index.as_view("index"), endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]

    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert interaction.name in thing_description.to_dict()["properties"]
        assert (
            thing_description.to_dict()["properties"][interaction.name]["forms"][1][
                "op"
            ]
            == "writeproperty"
        )

        assert (
            thing_description.to_dict()["properties"][interaction.name]["forms"][1][
                "htv:methodName"
            ]
            == "PUT"
        )
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)
