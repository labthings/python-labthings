import pytest

from labthings.server import labthing

from labthings.server.view import View
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
    assert 400 in app.error_handler_spec.get(None)


def test_init_app_no_error_formatter(app):
    thing = labthing.LabThing(format_flask_exceptions=False)
    thing.init_app(app)
    assert app.error_handler_spec == {}


def test_add_view(thing, view_cls, client):
    thing.add_view(view_cls, "/index", endpoint="index")

    with client as c:
        assert c.get("/index").data == b"GET"


def test_add_view_endpoint_clash(thing, view_cls, client):
    thing.add_view(view_cls, "/index", endpoint="index")
    with pytest.raises(AssertionError):
        thing.add_view(view_cls, "/index2", endpoint="index")


def test_view_decorator(thing, client):
    @thing.view("/index")
    class ViewClass(View):
        def get(self):
            return "GET"

    with client as c:
        assert c.get("/index").data == b"GET"


def test_add_view_action(thing, view_cls, client):
    view_cls.__apispec__ = {"_groups": ["actions"]}
    thing.add_view(view_cls, "/index", endpoint="index")
    assert view_cls in thing._action_views.values()


def test_add_view_property(thing, view_cls, client):
    view_cls.__apispec__ = {"_groups": ["properties"]}
    thing.add_view(view_cls, "/index", endpoint="index")
    assert view_cls in thing._property_views.values()


def test_init_app_early_views(app, view_cls, client):
    thing = labthing.LabThing()
    thing.add_view(view_cls, "/index", endpoint="index")

    thing.init_app(app)

    with client as c:
        assert c.get("/index").data == b"GET"


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


def test_url_for(thing, view_cls, app_ctx):
    with app_ctx.test_request_context():
        # Before added, should return no URL
        assert thing.url_for(view_cls) == ""
        # Add view
        thing.add_view(view_cls, "/index", endpoint="index")
        # Check URLs
        assert thing.url_for(view_cls, _external=False) == "/index"
        assert all(
            substring in thing.url_for(view_cls) for substring in ["http://", "/index"]
        )


def test_owns_endpoint(thing, view_cls, app_ctx):
    assert not thing.owns_endpoint("index")
    thing.add_view(view_cls, "/index", endpoint="index")
    assert thing.owns_endpoint("index")


def test_add_root_link(thing, view_cls, app_ctx, schemas_path):
    thing.add_root_link(view_cls, "rel")
    assert {
        "rel": "rel",
        "view": view_cls,
        "params": {},
        "kwargs": {},
    } in thing.thing_description._links


def test_td_add_link_options(thing, view_cls):
    thing.add_root_link(
        view_cls, "rel", kwargs={"kwarg": "kvalue"}, params={"param": "pvalue"}
    )
    assert {
        "rel": "rel",
        "view": view_cls,
        "params": {"param": "pvalue"},
        "kwargs": {"kwarg": "kvalue"},
    } in thing.thing_description._links


def test_root_rep(thing, app_ctx):
    with app_ctx.test_request_context():
        assert thing.root() == thing.thing_description.to_dict()


def test_description(thing):
    assert thing.description == ""
    thing.description = "description"
    assert thing.description == "description"
    assert thing.spec.description == "description"


def test_title(thing):
    assert thing.title == ""
    thing.title = "title"
    assert thing.title == "title"
    assert thing.spec.title == "title"


def test_version(thing):
    assert thing.version == "0.0.0"
    thing.version = "x.x.x"
    assert thing.version == "x.x.x"
    assert thing.spec.version == "x.x.x"


def test_socket_handler(thing, fake_websocket):
    ws = fake_websocket("", recieve_once=True)
    thing._socket_handler(ws)
    assert ws.response is None
