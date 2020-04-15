import pytest

from marshmallow import Schema as _Schema
from flask import make_response

from labthings.server.schema import Schema
from labthings.server import fields
from labthings.core.tasks.thread import TaskThread

from labthings.server import decorators


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
        return TaskThread()

    wrapped_func = decorators.marshal_task(func)

    with app_ctx.test_request_context():
        out = wrapped_func()
        common_task_test(out[0])


def test_marshal_task_response_tuple(app_ctx):
    def func():
        return (TaskThread(), 201, {})

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
