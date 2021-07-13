import pytest

from labthings import fields, schema
from labthings.actions.thread import ActionThread
from labthings.extensions import BaseExtension
from labthings.views import ActionView, PropertyView, EventView
from marshmallow import validate

def test_openapi(thing, action_view_cls):
    action_view_cls.args = {"n": fields.Integer()}
    thing.add_view(action_view_cls, "TestAction")

    class TestProperty(PropertyView):
        schema = {"count": fields.Integer()}
        def get(self):
            return 1
        def post(self, args):
            pass
    thing.add_view(TestProperty, "TestProperty")

    class TestFieldProperty(PropertyView):
        schema = fields.String(validate=validate.OneOf(["one", "two"]))
        def get(self):
            return "one"
        def post(self, args):
            pass
    thing.add_view(TestFieldProperty, "TestFieldProperty")
    
    
    thing.spec.to_yaml()