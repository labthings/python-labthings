import json
import time

import pytest
from flask import make_response
from werkzeug.http import parse_set_header
from werkzeug.wrappers import Response as ResponseBase

from labthings import views


def common_test(app):
    c = app.test_client()

    assert c.get("/").data == b"GET"
    assert c.post("/").data == b"POST"
    assert c.put("/").status_code == 405
    assert c.delete("/").status_code == 405
    meths = parse_set_header(c.open("/", method="OPTIONS").headers["Allow"])
    assert sorted(meths) == ["GET", "HEAD", "OPTIONS", "POST"]


def test_method_based_view(app):
    class Index(views.View):
        def get(self):
            return "GET"

        def post(self):
            return "POST"

    app.add_url_rule("/", view_func=Index.as_view("index"))
    common_test(app)


def test_view_patching(app):
    class Index(views.View):
        def get(self):
            1 // 0

        def post(self):
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
    class Index(views.View):
        def get(self):
            return {"key": "value"}

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.get("/")
        assert res.status_code == 200
        assert res.content_type == "application/json"
        assert json.loads(res.data) == {"key": "value"}


def test_return_response(app, client):
    class Index(views.View):
        def get(self):
            return make_response("GET", 200)

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.get("/")
        assert res.status_code == 200
        assert res.data == b"GET"


def test_missing_method(app, client):
    class Index(views.View):
        def get(self):
            return "GET"

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.post("/")
        assert res.status_code == 405


def test_missing_head_method(app, client):
    class Index(views.View):
        def get(self):
            return "GET"

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.head("/")
        assert res.status_code == 200


def test_get_value_text():
    class Index(views.View):
        def get(self):
            return "GET"

    # Main test
    assert Index().get_value() == "GET"


def test_get_value_missing():
    class Index(views.View):
        def post(self):
            return "POST"

    # Main test
    assert Index().get_value() is None


def test_get_value_raise_if_not_callable():
    class Index(views.View):
        def post(self):
            return "POST"

    Index.get = "GET"

    with pytest.raises(TypeError):
        # Main test
        Index().get_value()


def test_get_value_response_text(app_ctx):
    class Index(views.View):
        def get(self):
            return make_response("GET", 200)

    with app_ctx.test_request_context():
        assert isinstance(Index().get(), ResponseBase)
        assert Index().get().headers.get("Content-Type") == "text/html; charset=utf-8"
        # Main test
        assert Index().get_value() == b"GET"


def test_get_value_response_json(app_ctx):
    class Index(views.View):
        def get(self):
            return make_response({"json": "body"}, 200)

    with app_ctx.test_request_context():
        assert isinstance(Index().get(), ResponseBase)
        assert Index().get().headers.get("Content-Type") == "application/json"
        # Main test
        assert Index().get_value() == {"json": "body"}


def test_action_view_stop(app):
    class Index(views.ActionView):
        default_stop_timeout = 0

        def post(self):
            while True:
                time.sleep(1)

    app.add_url_rule("/", view_func=Index.as_view("index"))
    c = app.test_client()

    response = c.post("/")
    assert response.status_code == 201
    assert response.json.get("status") == "running"
    # Assert we only have a single running Action thread
    assert len(Index._deque) == 1
    action_thread = Index._deque[0]
    assert action_thread.default_stop_timeout == 0
    action_thread.stop()
    assert action_thread.status == "terminated"
