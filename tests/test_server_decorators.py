import pytest

from marshmallow import Schema as _Schema
from flask import make_response

from labthings.server.schema import Schema
from labthings.server import fields
from labthings.server.view import View
from labthings.core.tasks.thread import TaskThread

from labthings.server import decorators


@pytest.fixture
def empty_cls():
    class Index:
        pass

    return Index


def common_task_test(marshaled_task: dict):
    assert isinstance(marshaled_task, dict)
    assert isinstance(marshaled_task.get("id"), str)
    assert marshaled_task.get("function") == "None(args=(), kwargs={})"
    assert marshaled_task.get("status") == "idle"


def test_marshal_with_ma_schema():
    def func():
        obj = type("obj", (object,), {"integer": 1})
        return obj

    schema = _Schema.from_dict({"integer": fields.Int()})()
    wrapped_func = decorators.marshal_with(schema)(func)

    assert wrapped_func() == ({"integer": 1}, 200, {})


def test_marshal_with_dict_schema():
    def func():
        obj = type("obj", (object,), {"integer": 1})
        return obj

    schema = {"integer": fields.Int()}
    wrapped_func = decorators.marshal_with(schema)(func)

    assert wrapped_func() == ({"integer": 1}, 200, {})


def test_marshal_with_field_schema():
    def func():
        return 1

    schema = fields.String()
    wrapped_func = decorators.marshal_with(schema)(func)

    assert wrapped_func() == ("1", 200, {})


def test_marshal_with_response_tuple_field_schema(app_ctx):
    def func():
        return ("response", 200, {})

    schema = fields.String()
    wrapped_func = decorators.marshal_with(schema)(func)

    with app_ctx.test_request_context():
        assert wrapped_func() == ("response", 200, {})


def test_marshal_with_response_field_schema(app_ctx):
    def func():
        return make_response("response", 200)

    schema = fields.String()
    wrapped_func = decorators.marshal_with(schema)(func)

    with app_ctx.test_request_context():
        assert wrapped_func().data == b"response"


def test_marshal_with_invalid_schema():
    def func():
        return 1

    schema = object()
    with pytest.raises(TypeError):
        decorators.marshal_with(schema)(func)


def test_marshal_task(app_ctx):
    def func():
        return TaskThread(None)

    wrapped_func = decorators.marshal_task(func)

    with app_ctx.test_request_context():
        out = wrapped_func()
        common_task_test(out[0])


def test_marshal_task_response_tuple(app_ctx):
    def func():
        return (TaskThread(None), 201, {})

    wrapped_func = decorators.marshal_task(func)

    with app_ctx.test_request_context():
        out = wrapped_func()
        common_task_test(out[0])


def test_marshal_task_response_invalid(app_ctx):
    def func():
        return object()

    wrapped_func = decorators.marshal_task(func)

    with app_ctx.test_request_context(), pytest.raises(TypeError):
        wrapped_func()


def test_thing_action(empty_cls):
    wrapped_cls = decorators.thing_action(empty_cls)
    assert wrapped_cls.__apispec__["tags"] == set(["actions"])


def test_safe(empty_cls):
    wrapped_cls = decorators.safe(empty_cls)
    assert wrapped_cls.__apispec__["_safe"] == True


def test_idempotent(empty_cls):
    wrapped_cls = decorators.idempotent(empty_cls)
    assert wrapped_cls.__apispec__["_idempotent"] == True


def test_thing_property(view_cls):
    wrapped_cls = decorators.thing_property(view_cls)
    assert wrapped_cls.__apispec__["tags"] == set(["properties"])


def test_thing_property_empty_class(empty_cls, app_ctx):
    wrapped_cls = decorators.thing_property(empty_cls)
    assert wrapped_cls.__apispec__["tags"] == set(["properties"])


def test_thing_property_property_notify(view_cls, app_ctx):
    wrapped_cls = decorators.thing_property(view_cls)

    with app_ctx.test_request_context():
        wrapped_cls().post()


def test_property_schema(app, client):
    class Index(View):
        @staticmethod
        def get():
            obj = type("obj", (object,), {"integer": 1})
            return obj

        @staticmethod
        def post(args):
            i = args.get("integer")
            obj = type("obj", (object,), {"integer": i})
            return obj

        @staticmethod
        def put(args):
            i = args.get("integer")
            obj = type("obj", (object,), {"integer": i})
            return obj

    schema = _Schema.from_dict({"integer": fields.Int()})()
    WrappedCls = decorators.PropertySchema(schema)(Index)

    assert WrappedCls.__apispec__.get("_propertySchema") == schema

    app.add_url_rule("/", view_func=WrappedCls.as_view("index"))

    with client as c:
        assert c.get("/").json == {"integer": 1}
        assert c.post("/", json={"integer": 5}).json == {"integer": 5}
        assert c.put("/", json={"integer": 5}).json == {"integer": 5}


def test_property_schema_empty_class(empty_cls):
    schema = _Schema.from_dict({"integer": fields.Int()})()
    WrappedCls = decorators.PropertySchema(schema)(empty_cls)

    assert WrappedCls.__apispec__.get("_propertySchema") == schema


def test_use_body(app, client):
    class Index(View):
        @staticmethod
        def post(data):
            return str(data)

    schema = fields.Int()
    Index.post = decorators.use_body(schema)(Index.post)

    assert Index.post.__apispec__.get("_params") == schema

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client as c:
        assert c.post("/", data=b"5\n").data == b'"5"\n'


def test_use_body_required_no_data(app, client):
    class Index(View):
        @staticmethod
        def post(data):
            return {}

    schema = fields.Int(required=True)
    Index.post = decorators.use_body(schema)(Index.post)

    assert Index.post.__apispec__.get("_params") == schema

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client as c:
        assert c.post("/").status_code == 400


def test_use_body_no_data(app, client):
    class Index(View):
        @staticmethod
        def post(data):
            assert data is None
            return {}

    schema = fields.Int()
    Index.post = decorators.use_body(schema)(Index.post)

    assert Index.post.__apispec__.get("_params") == schema

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client as c:
        assert c.post("/").status_code == 200


def test_use_body_no_data_missing_given(app, client):
    class Index(View):
        @staticmethod
        def post(data):
            return str(data)

    schema = fields.Int(missing=5)
    Index.post = decorators.use_body(schema)(Index.post)

    assert Index.post.__apispec__.get("_params") == schema

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client as c:
        assert c.post("/").data == b'"5"\n'


def test_use_body_malformed(app, client):
    class Index(View):
        @staticmethod
        def post(data):
            return {}

    schema = fields.Int(required=True)
    Index.post = decorators.use_body(schema)(Index.post)

    assert Index.post.__apispec__.get("_params") == schema

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client as c:
        assert c.post("/", data=b"{}").status_code == 400


def test_use_args(app, client):
    class Index(View):
        @staticmethod
        def post(data):
            return data

    schema = _Schema.from_dict({"integer": fields.Int()})()
    Index.post = decorators.use_args(schema)(Index.post)

    assert Index.post.__apispec__.get("_params") == schema

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client as c:
        assert c.post("/", json={"integer": 5}).json == {"integer": 5}


def test_use_args_field(app, client):
    class Index(View):
        @staticmethod
        def post(data):
            return str(data)

    schema = fields.Int(missing=5)
    Index.post = decorators.use_args(schema)(Index.post)

    assert Index.post.__apispec__.get("_params") == schema

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client as c:
        assert c.post("/").data == b'"5"\n'


def test_doc(empty_cls):
    wrapped_cls = decorators.doc(key="value")(empty_cls)
    assert wrapped_cls.__apispec__["key"] == "value"


def test_tag(empty_cls):
    wrapped_cls = decorators.tag(["tag", "tag2"])(empty_cls)
    assert wrapped_cls.__apispec__["tags"] == set(["tag", "tag2"])


def test_tag_single(empty_cls):
    wrapped_cls = decorators.tag("tag")(empty_cls)
    assert wrapped_cls.__apispec__["tags"] == set(["tag"])


def test_tag_invalid(empty_cls):
    with pytest.raises(TypeError):
        decorators.tag(object())(empty_cls)


def test_doc_response(empty_cls):
    wrapped_cls = decorators.doc_response(
        200, description="description", mimetype="text/plain", key="value"
    )(empty_cls)
    assert wrapped_cls.__apispec__ == {
        "responses": {
            200: {
                "description": "description",
                "key": "value",
                "content": {"text/plain": {}},
            }
        },
        "_content_type": "text/plain",
    }


def test_doc_response_no_mimetype(empty_cls):
    wrapped_cls = decorators.doc_response(200)(empty_cls)
    assert wrapped_cls.__apispec__ == {"responses": {200: {"description": "OK"}}}
