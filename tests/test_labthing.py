import pytest

from labthings import LabThing

from labthings.views import View, ActionView, PropertyView
from labthings.representations import LabThingsJSONEncoder
from labthings.names import EXTENSION_NAME
from labthings.extensions import BaseExtension


def test_init_types():
    types = ["org.labthings.test"]
    thing = LabThing(types=types)
    assert thing.types == types


def test_init_types_invalid():
    types = ["org;labthings;test"]
    with pytest.raises(ValueError):
        LabThing(types=types)


def test_init_app(app):
    thing = LabThing()
    thing.init_app(app)

    # Check weakref
    assert app.extensions.get(EXTENSION_NAME)() == thing

    assert app.json_encoder == LabThingsJSONEncoder
    assert 400 in app.error_handler_spec.get(None)


def test_init_app_no_error_formatter(app):
    thing = LabThing(format_flask_exceptions=False)
    thing.init_app(app)
    assert app.error_handler_spec == {}


def test_add_view(thing, view_cls, client):
    thing.add_view(view_cls, "/index", endpoint="index")

    with client as c:
        assert c.get("/index").data == b'"GET"\n'


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
        assert c.get("/index").data == b'"GET"\n'


def test_add_view_action(thing, client):
    thing.add_view(ActionView, "/index", endpoint="index")
    assert "index" in thing.actions


def test_add_view_property(thing, view_cls, client):
    thing.add_view(PropertyView, "/index", endpoint="index")
    assert "index" in thing.properties


def test_init_app_early_views(app, view_cls, client):
    thing = LabThing()
    thing.add_view(view_cls, "/index", endpoint="index")

    thing.init_app(app)

    with client as c:
        assert c.get("/index").data == b'"GET"\n'


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


def test_safe_title(thing):
    assert thing.title == ""
    assert thing.safe_title == "unknown"
    thing.title = "Example LabThing 001"
    assert thing.safe_title == "examplelabthing001"


def test_version(thing):
    assert thing.version == "0.0.0"
    thing.version = "x.x.x"
    assert thing.version == "x.x.x"
    assert thing.spec.version == "x.x.x"


def test_build_property(thing):
    obj = type("obj", (object,), {"property_name": "propertyValue"})

    thing.build_property(obj, "property_name")
    # -1 index for last view added
    # 1 index for URL tuple
    assert "type_property_name" in thing.properties


def test_build_action(thing):
    def f():
        return "response"

    obj = type("obj", (object,), {"f": f})

    thing.build_action(obj, "f")
    # -1 index for last view added
    # 1 index for URL tuple
    assert "type_f" in thing.actions
