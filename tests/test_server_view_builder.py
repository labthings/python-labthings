from labthings.server.view import builder
from labthings.server import fields


def test_property_of_no_schema(app, client):
    obj = type("obj", (object,), {"property_name": "propertyValue"})

    # GeneratedClass = builder.property_of(obj, "property_name", schema=fields.String())
    GeneratedClass = builder.property_of(obj, "property_name")
    app.add_url_rule("/", view_func=GeneratedClass.as_view("index"))

    with client as c:
        assert c.get("/").data == b'"propertyValue"\n'
        assert c.put("/", data="newPropertyValue").data == b'"newPropertyValue"\n'
        assert c.get("/").data == b'"newPropertyValue"\n'


def test_property_of_with_schema(app, client):
    obj = type("obj", (object,), {"property_name": "propertyValue"})

    # GeneratedClass = builder.property_of(obj, "property_name", schema=fields.String())
    GeneratedClass = builder.property_of(obj, "property_name", schema=fields.String())
    app.add_url_rule("/", view_func=GeneratedClass.as_view("index"))

    with client as c:
        assert c.get("/").data == b'"propertyValue"\n'
        assert c.put("/", data="newPropertyValue").data == b'"newPropertyValue"\n'
        assert c.get("/").data == b'"newPropertyValue"\n'


def test_property_of_dict(app, client):
    obj = type(
        "obj",
        (object,),
        {
            "properties": {
                "property_name": "propertyValue",
                "property_name_2": "propertyValue2",
            }
        },
    )

    GeneratedClass = builder.property_of(
        obj,
        "properties",
        schema={"property_name": fields.String(), "property_name_2": fields.String(),},
    )
    app.add_url_rule("/", view_func=GeneratedClass.as_view("index"))

    with client as c:
        assert c.get("/").json == {
            "property_name": "propertyValue",
            "property_name_2": "propertyValue2",
        }
        assert c.put("/", json={"property_name": "newPropertyValue"}).json == {
            "property_name": "newPropertyValue",
            "property_name_2": "propertyValue2",
        }


def test_property_of_readonly():
    obj = type("obj", (object,), {"property_name": "propertyValue"})

    GeneratedClass = builder.property_of(obj, "property_name", readonly=True)

    assert callable(GeneratedClass.get)
    assert not hasattr(GeneratedClass, "post")


def test_property_of_name_description():
    obj = type("obj", (object,), {"property_name": "propertyValue"})
    GeneratedClass = builder.property_of(
        obj, "property_name", name="property_name", description="property description"
    )

    assert GeneratedClass.description == "property description"
    assert GeneratedClass.summary == "property description"


def test_action_from_with_args(app, client):
    def f(arg1, arg2=0):
        return {"arg1": arg1, "arg2": arg2}

    GeneratedClass = builder.action_from(
        f, args={"arg1": fields.Int(), "arg2": fields.Int(required=False)}
    )
    app.add_url_rule("/", view_func=GeneratedClass.as_view("index"))

    with client as c:
        input_json = {"arg1": 5}
        response = c.post("/", json=input_json).json
        assert "status" in response
        assert response["input"] == input_json


def test_action_from(debug_app, debug_client):
    def f():
        return "response"

    GeneratedClass = builder.action_from(f)
    debug_app.add_url_rule("/", view_func=GeneratedClass.as_view("index"))

    with debug_client as c:
        response = c.post("/").json
        assert "status" in response


def test_action_from_options(app):
    def f():
        return "response"

    assert builder.action_from(
        f,
        name="action_name",
        description="action_description",
        safe=True,
        idempotent=True,
    )


def test_static_from(app, client, app_ctx, static_path):

    GeneratedClass = builder.static_from(static_path,)
    app.add_url_rule("/static", view_func=GeneratedClass.as_view("index"))

    with app_ctx.test_request_context():
        assert GeneratedClass().get("text").status_code == 200

    with client as c:
        assert c.get("/static/text").data == b"text"


def test_static_from_options(app, app_ctx, static_path):
    assert builder.static_from(static_path, name="static_name")
