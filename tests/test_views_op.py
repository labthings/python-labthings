import pytest

from labthings.views import View, op


@pytest.fixture
def thing_description(thing):
    return thing.thing_description


def test_op_readproperty(helpers, app, thing_description, app_ctx, schemas_path):
    class Index(View):
        @op.readproperty
        def get(self):
            return "GET"

    app.add_url_rule("/", view_func=Index.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.property(rules, Index)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict()["properties"]
        assert (
            thing_description.to_dict()["properties"]["index"]["forms"][0]["op"]
            == "readproperty"
        )

        assert (
            thing_description.to_dict()["properties"]["index"]["forms"][0][
                "htv:methodName"
            ]
            == "GET"
        )
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_op_writeproperty(helpers, app, thing_description, app_ctx, schemas_path):
    class Index(View):
        @op.writeproperty
        def put(self):
            return "PUT"

    app.add_url_rule("/", view_func=Index.as_view("index"))
    rules = app.url_map._rules_by_endpoint["index"]

    thing_description.property(rules, Index)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict()["properties"]
        assert (
            thing_description.to_dict()["properties"]["index"]["forms"][0]["op"]
            == "writeproperty"
        )

        assert (
            thing_description.to_dict()["properties"]["index"]["forms"][0][
                "htv:methodName"
            ]
            == "PUT"
        )
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)
