import pytest

from labthings.server import labthing

from labthings.server.representations import LabThingsJSONEncoder
from labthings.server.names import EXTENSION_NAME
from labthings.server.extensions import BaseExtension


def test_init_types():
    types = ["org.labthings.test"]
    thing = labthing.LabThing(types=types)
    assert thing.types == types


def test_init_types_invalid():
    types = ["org;labthings;test"]
    with pytest.raises(ValueError):
        labthing.LabThing(types=types)


def test_init_app(app):
    thing = labthing.LabThing()
    thing.init_app(app)

    assert app.extensions.get(EXTENSION_NAME) == thing
    assert app.json_encoder == LabThingsJSONEncoder


def test_init_app_early_views(app, view_cls, client):
    thing = labthing.LabThing()
    thing.add_view(view_cls, "/", endpoint="index")

    thing.init_app(app)

    with client as c:
        assert c.get("/").status_code == 200


def test_register_extension(thing):
    extension = BaseExtension("org.labthings.tests.extension")
    thing.register_extension(extension)
    assert thing.extensions.get("org.labthings.tests.extension") == extension


def test_register_extension_type_error(thing):
    extension = object()
    with pytest.raises(TypeError):
        thing.register_extension(extension)


def test_add_component(thing):
    component = type("component", (object,), {})

    thing.add_component(component, "org.labthings.tests.component")
    assert "org.labthings.tests.component" in thing.components


def test_on_component_callback(thing):
    # Build extension
    def f(component):
        component.callback_called = True

    extension = BaseExtension("org.labthings.tests.extension")
    extension.on_component("org.labthings.tests.component", f)
    # Add extension
    thing.register_extension(extension)

    # Build component
    component = type("component", (object,), {"callback_called": False})

    # Add component
    thing.add_component(component, "org.labthings.tests.component")
    # Check callback
    assert component.callback_called


def test_on_component_callback_component_already_added(thing):
    # Build component
    component = type("component", (object,), {"callback_called": False})
    # Add component
    thing.add_component(component, "org.labthings.tests.component")

    # Build extension
    def f(component):
        component.callback_called = True

    extension = BaseExtension("org.labthings.tests.extension")
    extension.on_component("org.labthings.tests.component", f)
    # Add extension
    thing.register_extension(extension)

    # Check callback
    assert component.callback_called


def test_on_component_callback_wrong_component(thing):
    def f(component):
        component.callback_called = True

    extension = BaseExtension("org.labthings.tests.extension")
    extension.on_component("org.labthings.tests.component", f)
    thing.register_extension(extension)

    component = type("component", (object,), {"callback_called": False})
    thing.add_component(component, "org.labthings.tests.wrong_component")
    assert not component.callback_called


def test_on_register_callback(thing):
    # Build extension
    def f(extension):
        extension.callback_called = True

    extension = BaseExtension("org.labthings.tests.extension")
    extension.callback_called = False
    extension.on_register(f, args=(extension,))
    # Add extension
    thing.register_extension(extension)

    # Check callback
    assert extension.callback_called


def test_complete_url(thing):
    thing.url_prefix = ""
    assert thing._complete_url("", "") == "/"
    assert thing._complete_url("", "api") == "/api"
    assert thing._complete_url("/method", "api") == "/api/method"

    thing.url_prefix = "prefix"
    assert thing._complete_url("", "") == "/prefix"
    assert thing._complete_url("", "api") == "/prefix/api"
    assert thing._complete_url("/method", "api") == "/prefix/api/method"
