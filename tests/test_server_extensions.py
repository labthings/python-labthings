from labthings.server import extensions
import os

import pytest


@pytest.fixture
def lt_extension():
    return extensions.BaseExtension("org.labthings.tests.extension")


def test_extension_init(lt_extension):
    assert lt_extension
    assert lt_extension.name


def test_add_view(lt_extension, app, view_cls):
    lt_extension.add_view(view_cls, "/index", endpoint="index")

    assert "index" in lt_extension.views
    assert lt_extension.views.get("index") == {
        "urls": ["/org.labthings.tests.extension/index"],
        "view": view_cls,
        "kwargs": {},
    }


def test_on_register(lt_extension):
    def f(arg, kwarg=1):
        pass

    lt_extension.on_register(f, args=(1,), kwargs={"kwarg": 0})
    assert {
        "function": f,
        "args": (1,),
        "kwargs": {"kwarg": 0},
    } in lt_extension._on_registers


def test_on_register_non_callable(lt_extension):
    with pytest.raises(TypeError):
        lt_extension.on_register(object())


def test_on_component(lt_extension):
    def f():
        pass

    lt_extension.on_component("org.labthings.tests.component", f)
    assert {
        "component": "org.labthings.tests.component",
        "function": f,
        "args": (),
        "kwargs": {},
    } in lt_extension._on_components


def test_on_component_non_callable(lt_extension):
    with pytest.raises(TypeError):
        lt_extension.on_component("org.labthings.tests.component", object())


def test_meta_simple(lt_extension):
    lt_extension.add_meta("key", "value")
    assert lt_extension.meta.get("key") == "value"


def test_meta_callable(lt_extension):
    def f():
        return "callable value"

    lt_extension.add_meta("key", f)
    assert lt_extension.meta.get("key") == "callable value"


def test_add_method(lt_extension):
    def f():
        pass

    lt_extension.add_method(
        f, "method_name",
    )
    assert lt_extension.method_name == f


def test_add_method_name_clash(lt_extension):
    def f():
        pass

    lt_extension.add_method(
        f, "method_name",
    )
    assert lt_extension.method_name == f

    with pytest.raises(NameError):
        lt_extension.add_method(
            f, "method_name",
        )


# TODO: Rewrite static file tests to attach the extension to a Thing instance


def test_find_instances_in_module(lt_extension):
    mod = type(
        "mod",
        (object,),
        {"extension_instance": lt_extension, "another_object": object()},
    )
    assert extensions.find_instances_in_module(mod, extensions.BaseExtension) == [
        lt_extension
    ]


def test_find_extensions_in_file(extensions_path):
    test_file = os.path.join(extensions_path, "extension.py")

    found_extensions = extensions.find_extensions_in_file(test_file)
    assert len(found_extensions) == 1
    assert found_extensions[0].name == "org.labthings.tests.extension"


def test_find_extensions_in_file_explicit_list(extensions_path):
    test_file = os.path.join(extensions_path, "extension_explicit_list.py")

    found_extensions = extensions.find_extensions_in_file(test_file)
    assert len(found_extensions) == 1
    assert found_extensions[0].name == "org.labthings.tests.extension"


def test_find_extensions_in_file_exception(extensions_path):
    test_file = os.path.join(extensions_path, "extension_exception.py")

    found_extensions = extensions.find_extensions_in_file(test_file)
    assert found_extensions == []


def test_find_extensions(extensions_path):
    found_extensions = extensions.find_extensions(extensions_path)
    assert len(found_extensions) == 3
