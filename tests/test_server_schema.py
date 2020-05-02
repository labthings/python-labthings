from labthings.server import schema
from labthings.server import fields

from labthings.core.tasks.thread import TaskThread
from labthings.server.extensions import BaseExtension


def test_field_schema(app_ctx):
    test_schema = schema.FieldSchema(fields.String())

    assert test_schema.serialize(5) == "5"
    assert test_schema.dump(5) == "5"
    assert test_schema.deserialize("string") == "string"


def test_task_schema(app_ctx):
    test_schema = schema.TaskSchema()
    test_task_thread = TaskThread(None)

    with app_ctx.test_request_context():
        d = test_schema.dump(test_task_thread)
        assert isinstance(d, dict)
        assert "data" in d
        assert "links" in d
        assert isinstance(d.get("links"), dict)
        assert "self" in d.get("links")
        assert d.get("function") == "None(args=(), kwargs={})"


def test_extension_schema(app_ctx):
    test_schema = schema.ExtensionSchema()
    test_extension = BaseExtension("org.labthings.tests.extension")

    with app_ctx.test_request_context():
        d = test_schema.dump(test_extension)
        assert isinstance(d, dict)
        assert "pythonName" in d
        assert d.get("pythonName") == "org.labthings.tests.extension"
        assert "links" in d
        assert isinstance(d.get("links"), dict)
