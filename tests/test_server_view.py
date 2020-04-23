from labthings.server import view
from werkzeug.http import parse_set_header
from werkzeug.wrappers import Response as ResponseBase
from flask import make_response

import pytest


def common_test(app):
    c = app.test_client()

    assert c.get("/").data == b"GET"
    assert c.post("/").data == b"POST"
    assert c.put("/").status_code == 405
    assert c.delete("/").status_code == 405
    meths = parse_set_header(c.open("/", method="OPTIONS").headers["Allow"])
    assert sorted(meths) == ["GET", "HEAD", "OPTIONS", "POST"]


def test_method_based_view(app):
    class Index(view.View):
        @staticmethod
        def get():
            return "GET"

        @staticmethod
        def post():
            return "POST"

    app.add_url_rule("/", view_func=Index.as_view("index"))
    common_test(app)


def test_view_patching(app):
    class Index(view.View):
        @staticmethod
        def get():
            1 // 0

        @staticmethod
        def post():
            1 // 0

    class Other(Index):
        def get(self):
            return "GET"

        def post(self):
            return "POST"

    view_obj = Index.as_view("index")
    view_obj.view_class = Other
    app.add_url_rule("/", view_func=view_obj)
    common_test(app)


def test_accept_default_application_json(app, client):
    class Index(view.View):
        @staticmethod
        def get():
            return "GET"

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.get("/", headers=[("Accept", "application/json")])
        assert res.status_code == 200
        assert res.content_type == "application/json"


def test_return_response(app, client):
    class Index(view.View):
        @staticmethod
        def get():
            return make_response("GET", 200)

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.get("/", headers=[("Accept", "application/json")])
        assert res.status_code == 200
        assert res.data == b"GET"


def test_missing_method(app, client):
    class Index(view.View):
        @staticmethod
        def get():
            return "GET"

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.post("/", headers=[("Accept", "application/json")])
        assert res.status_code == 405


def test_missing_head_method(app, client):
    class Index(view.View):
        @staticmethod
        def get():
            return "GET"

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.head("/")
        assert res.status_code == 200


def test_get_value_text():
    class Index(view.View):
        @staticmethod
        def get():
            return "GET"

    assert Index().get_value() == "GET"


def test_get_value_missing():
    class Index(view.View):
        @staticmethod
        def post():
            return "POST"

    assert Index().get_value() is None


def test_get_value_raise_if_not_callable():
    class Index(view.View):
        @staticmethod
        def post():
            return "POST"

    Index.get = "GET"

    with pytest.raises(TypeError):
        Index().get_value()


def test_get_value_response_text(app_ctx):
    class Index(view.View):
        @staticmethod
        def get():
            return make_response("GET", 200)

    with app_ctx.test_request_context():
        assert isinstance(Index().get(), ResponseBase)
        assert Index().get().json is None
        assert Index().get_value() == "GET"


def test_get_value_response_json(app_ctx):
    class Index(view.View):
        @staticmethod
        def get():
            return make_response({"json": "body"}, 200)

    with app_ctx.test_request_context():
        assert isinstance(Index().get(), ResponseBase)
        assert Index().get().json is not None
        assert Index().get_value() == {"json": "body"}
