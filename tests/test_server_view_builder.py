import pytest

from labthings.server.view import builder


def test_property_of(app):
    obj = type("obj", (object,), {"property_name": "propertyValue"})

    GeneratedClass = builder.property_of(obj, "property_name")

    assert callable(GeneratedClass.get)
    assert callable(GeneratedClass.post)

    app.add_url_rule("/", view_func=GeneratedClass.as_view("index"))

    with app.test_client() as c:
        assert c.get("/").data == b"propertyValue"
        assert c.post("/", data=b"newPropertyValue").data == b"newPropertyValue"
        assert c.get("/").data == b"newPropertyValue"


def test_property_of_dict(app):
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

    GeneratedClass = builder.property_of(obj, "properties")

    assert callable(GeneratedClass.get)
    assert callable(GeneratedClass.post)
    assert callable(GeneratedClass.put)

    app.add_url_rule("/", view_func=GeneratedClass.as_view("index"))

    with app.test_client() as c:
        assert (
            c.get("/").data
            == b'{"property_name":"propertyValue","property_name_2":"propertyValue2"}\n'
        )
        assert (
            c.put("/", json={"property_name": "newPropertyValue"}).data
            == b'{"property_name":"newPropertyValue","property_name_2":"propertyValue2"}\n'
        )
        assert (
            c.post("/", json={"property_name": "newPropertyValue"}).data
            == b'{"property_name":"newPropertyValue"}\n'
        )


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

    assert GeneratedClass.__apispec__.get("description") == "property description"
    assert GeneratedClass.__apispec__.get("summary") == "property description"
