from labthings import find

from labthings.extensions import BaseExtension


def test_current_labthing(thing, thing_ctx):
    with thing_ctx.test_request_context():
        assert find.current_labthing() is thing


def test_current_labthing_explicit_app(thing, thing_ctx):
    with thing_ctx.test_request_context():
        assert find.current_labthing(thing.app) is thing


def test_current_labthing_missing_app():
    assert find.current_labthing() is None


def test_registered_extensions(thing_ctx):
    with thing_ctx.test_request_context():
        assert find.registered_extensions() == {}


def test_registered_extensions_explicit_thing(thing):
    assert find.registered_extensions(thing) == {}


def test_registered_components(thing_ctx):
    with thing_ctx.test_request_context():
        assert find.registered_components() == {}


def test_registered_components_explicit_thing(thing):
    assert find.registered_components(thing) == {}


def test_find_component(thing, thing_ctx):
    component = type("component", (object,), {})
    thing.add_component(component, "org.labthings.tests.component")

    with thing_ctx.test_request_context():
        assert find.find_component("org.labthings.tests.component") == component


def test_find_component_explicit_thing(thing):
    component = type("component", (object,), {})
    thing.add_component(component, "org.labthings.tests.component")

    assert find.find_component("org.labthings.tests.component", thing) == component


def test_find_component_missing_component(thing_ctx):
    with thing_ctx.test_request_context():
        assert find.find_component("org.labthings.tests.component") is None


def test_find_extension(thing, thing_ctx):
    extension = BaseExtension("org.labthings.tests.extension")
    thing.register_extension(extension)

    with thing_ctx.test_request_context():
        assert find.find_extension("org.labthings.tests.extension") == extension


def test_find_extension_explicit_thing(thing):
    extension = BaseExtension("org.labthings.tests.extension")
    thing.register_extension(extension)

    assert find.find_extension("org.labthings.tests.extension", thing) == extension


def test_find_extension_missing_extesion(thing_ctx):
    with thing_ctx.test_request_context():
        assert find.find_extension("org.labthings.tests.extension") is None
