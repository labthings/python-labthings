# -*- coding: utf-8 -*-
from flask import jsonify, url_for
import marshmallow

from .names import TASK_ENDPOINT, TASK_LIST_ENDPOINT, EXTENSION_LIST_ENDPOINT
from .utilities import view_class_from_endpoint, description_from_view
from . import fields

MARSHMALLOW_VERSION_INFO = tuple(
    [int(part) for part in marshmallow.__version__.split(".") if part.isdigit()]
)

sentinel = object()


class Schema(marshmallow.Schema):
    """Base serializer with which to define custom serializers.
    See `marshmallow.Schema` for more details about the `Schema` API.
    """

    def jsonify(self, obj, *args, many=sentinel, **kwargs):
        """Return a JSON response containing the serialized data.
        :param obj: Object to serialize.
        :param bool many: Whether `obj` should be serialized as an instance
            or as a collection. If unset, defaults to the value of the
            `many` attribute on this Schema.
        :param kwargs: Additional keyword arguments passed to `flask.jsonify`.
        .. versionchanged:: 0.6.0
            Takes the same arguments as `marshmallow.Schema.dump`. Additional
            keyword arguments are passed to `flask.jsonify`.
        .. versionchanged:: 0.6.3
            The `many` argument for this method defaults to the value of
            the `many` attribute on the Schema. Previously, the `many`
            argument of this method defaulted to False, regardless of the
            value of `Schema.many`.
        """
        if many is sentinel:
            many = self.many
        if MARSHMALLOW_VERSION_INFO[0] >= 3:
            data = self.dump(obj, many=many)
        else:
            data = self.dump(obj, many=many).data
        return jsonify(data, *args, **kwargs)


class FieldSchema:
    """
    "Virtual schema" for handling individual fields treated as schemas.

    For example, when serializing/deserializing individual values that are not
    attributes of an object.
    """

    def __init__(self, field: fields.Field):
        """Create a converter for data of the field type

        Args:
            field (Field): Marshmallow Field type of data
        """
        self.field = field

    def deserialize(self, value):
        return self.field.deserialize(value)

    def serialize(self, value):
        """Serialize a value to Field type

        Args:
            value: Data to serialize

        Returns:
            Serialized data
        """
        obj = type("obj", (object,), {"value": value})

        return self.field.serialize("value", obj)

    def jsonify(self, value):
        """Serialize a value to JSON

        Args:
            value: Data to serialize

        Returns:
            Serialized JSON data
        """
        return jsonify(self.serialize(value))


class TaskSchema(Schema):
    _ID = fields.String(data_key="id")
    target_string = fields.String(data_key="function")
    _status = fields.String(data_key="status")
    progress = fields.String()
    data = fields.Raw()
    _return_value = fields.Raw(data_key="return")
    _start_time = fields.String(data_key="start_time")
    _end_time = fields.String(data_key="end_time")
    log = fields.List(fields.Dict())

    links = fields.Dict()

    @marshmallow.pre_dump
    def generate_links(self, data, **kwargs):
        data.links = {
            "self": {
                "href": url_for(TASK_ENDPOINT, task_id=data.id, _external=True),
                "mimetype": "application/json",
                **description_from_view(view_class_from_endpoint(TASK_ENDPOINT)),
            }
        }
        return data


class ExtensionSchema(Schema):
    name = fields.String(data_key="title")
    _name_python_safe = fields.String(data_key="pythonName")
    _cls = fields.String(data_key="pythonObject")
    meta = fields.Dict()
    description = fields.String()

    links = fields.Dict()

    @marshmallow.pre_dump
    def generate_links(self, data, **kwargs):
        d = {}
        for view_id, view_data in data.views.items():
            view_cls = view_data["view"]
            view_rule = view_data["rule"]
            # Make links dictionary if it doesn't yet exist
            d[view_id] = {
                "href": url_for(EXTENSION_LIST_ENDPOINT, _external=True) + view_rule,
                **description_from_view(view_cls),
            }

        data.links = d

        return data
