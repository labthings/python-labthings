from labthings.views import Interaction, Property, Action
from labthings.representations import DEFAULT_REPRESENTATIONS


def test_interaction_defaults():
    i = Interaction("name", title="Title")
    assert i.name == "name"
    assert i.title == "Title"

    assert i.content_type == i.response_content_type == "application/json"

    assert i._methodmap == {}
    assert i._representations == DEFAULT_REPRESENTATIONS


def test_interaction_methods():
    i = Interaction("name", title="Title")
    i._methodmap = {
        "get": "get_meth",
        "post": "post_meth",
        "put": "missing_meth",
        "not_http": "not_http_meth",
    }

    i.get_meth = lambda: True
    i.post_meth = lambda: True
    i.not_http_meth = lambda: True

    assert i.methods == set(["get", "post"])


def test_interaction_binding():
    i = Interaction("name", title="Title")

    i.bind_method("get", "get_meth")
    assert i._methodmap["get"] == "get_meth"

    i.unbind_method("get")
    assert "get" not in i._methodmap

    i.bind_websocket("ws_meth")
    assert i._methodmap["websocket"] == "ws_meth"

    i.unbind_websocket()
    assert "websocket" not in i._methodmap
