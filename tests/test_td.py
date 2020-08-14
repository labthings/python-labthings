import pytest

from labthings import fields

from labthings.interactions import Action, Property


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


def test_td_action(helpers, app, thing_description, app_ctx, schemas_path):
    interaction = Action("index", None, None)

    app.add_url_rule("/", view_func=interaction, endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]
    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("actions")
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_action_with_schema(helpers, app, thing_description, app_ctx, schemas_path):
    interaction = Action(
        "index", None, None, args={"integer": fields.Int()}, semtype="ToggleAction"
    )

    app.add_url_rule("/", view_func=interaction, endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]
    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("actions")

        assert thing_description.to_dict().get("actions").get("index") == {
            "title": "index",
            "description": "",
            "links": [{"href": "/"}],
            "safe": False,
            "idempotent": False,
            "forms": [
                {
                    "op": "invokeaction",
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
    interaction = Property("index", None, None)

    app.add_url_rule("/", view_func=interaction, endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]
    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("properties")
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_property_with_schema(
    helpers, app, thing_description, app_ctx, schemas_path
):
    interaction = Property("index", None, None, schema=fields.Int(required=True))

    app.add_url_rule("/", view_func=interaction, endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]
    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("properties")
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_property_with_url_param(
    helpers, app, thing_description, app_ctx, schemas_path
):
    interaction = Property("index", None, None)

    app.add_url_rule(
        "/path/<int:id>/", view_func=interaction, endpoint=interaction.name
    )
    rules = app.url_map._rules_by_endpoint[interaction.name]
    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict().get("properties")
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_property_post_to_write(
    helpers, app, thing_description, app_ctx, schemas_path
):
    interaction = Property("index", None, None)
    interaction.bind_method("post", "writeproperty")
    interaction.unbind_method("put")

    app.add_url_rule("/", view_func=interaction, endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]
    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict()["properties"]
        assert (
            thing_description.to_dict()["properties"]["index"]["forms"][1]["op"]
            == "writeproperty"
        )

        assert (
            thing_description.to_dict()["properties"]["index"]["forms"][1][
                "htv:methodName"
            ]
            == "POST"
        )
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_property_different_content_type(
    helpers, app, thing_description, app_ctx, schemas_path
):
    interaction = Property("index", None, None)
    interaction.content_type = "text/plain; charset=us-ascii"

    app.add_url_rule("/", view_func=interaction, endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]
    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict()["properties"]
        for form in thing_description.to_dict()["properties"]["index"]["forms"]:
            assert form["contentType"] == "text/plain; charset=us-ascii"
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)


def test_td_action_different_response_type(
    helpers, app, thing_description, app_ctx, schemas_path
):

    interaction = Action("index", None, None)
    interaction.response_content_type = "text/plain; charset=us-ascii"

    app.add_url_rule("/", view_func=interaction, endpoint=interaction.name)
    rules = app.url_map._rules_by_endpoint[interaction.name]
    thing_description.add(rules, interaction)

    with app_ctx.test_request_context():
        assert "index" in thing_description.to_dict()["actions"]
        for form in thing_description.to_dict()["actions"]["index"]["forms"]:
            assert form["response"]["contentType"] == "text/plain; charset=us-ascii"
        helpers.validate_thing_description(thing_description, app_ctx, schemas_path)
