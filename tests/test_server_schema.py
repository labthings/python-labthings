from labthings.server import schema
from labthings.server import fields

from labthings.core.tasks.thread import TaskThread
from labthings.server.extensions import BaseExtension


def test_schema_json(app_ctx):
    test_schema = schema.Schema.from_dict({"i": fields.Int(), "s": fields.String(),})()

    obj = type("obj", (object,), {"i": 5, "s": "string"})

    with app_ctx.test_request_context():
        assert test_schema.jsonify(obj).data == b'{"i":5,"s":"string"}\n'


def test_schema_many(app_ctx):
    test_schema = schema.Schema.from_dict({"i": fields.Int(), "s": fields.String(),})(
        many=True
    )

    obj1 = type("obj1", (object,), {"i": 5, "s": "string1"})
    obj2 = type("obj2", (object,), {"i": 5, "s": "string2"})
    objs = [obj1, obj2]

    with app_ctx.test_request_context():
        assert (
            test_schema.jsonify(objs).data
            == b'[{"i":5,"s":"string1"},{"i":5,"s":"string2"}]\n'
        )


def test_schema_json_many(app_ctx):
    test_schema = schema.Schema.from_dict({"i": fields.Int(), "s": fields.String(),})()

    obj1 = type("obj1", (object,), {"i": 5, "s": "string1"})
    obj2 = type("obj2", (object,), {"i": 5, "s": "string2"})
    objs = [obj1, obj2]

    with app_ctx.test_request_context():
        assert (
            test_schema.jsonify(objs, many=True).data
            == b'[{"i":5,"s":"string1"},{"i":5,"s":"string2"}]\n'
        )


def test_field_schema(app_ctx):
    test_schema = schema.FieldSchema(fields.String())

    assert test_schema.serialize(5) == "5"
    assert test_schema.dump(5) == "5"
    assert test_schema.deserialize("string") == "string"
    assert test_schema.jsonify(5).data == b'"5"\n'


def test_task_schema(app_ctx):
    test_schema = schema.TaskSchema()
    test_task_thread = TaskThread()

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
