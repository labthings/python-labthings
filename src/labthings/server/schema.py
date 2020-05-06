# -*- coding: utf-8 -*-
from flask import url_for
from werkzeug.routing import BuildError
from marshmallow import Schema, pre_dump

from .names import TASK_ENDPOINT, EXTENSION_LIST_ENDPOINT
from .utilities import view_class_from_endpoint, description_from_view
from . import fields

__all__ = ["Schema", "FieldSchema", "TaskSchema", "ExtensionSchema"]


class FieldSchema(Schema):
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
        Schema.__init__(self)
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

    def dump(self, value):
        return self.serialize(value)


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

    @pre_dump
    def generate_links(self, data, **kwargs):
        try:
            url = url_for(TASK_ENDPOINT, task_id=data.id, _external=True)
        except BuildError:
            url = None
        data.links = {
            "self": {
                "href": url,
                "mimetype": "application/json",
                **description_from_view(view_class_from_endpoint(TASK_ENDPOINT)),
            }
        }
        return data


class ActionSchema(Schema):
    _ID = fields.String(data_key="id")
    _status = fields.String(data_key="status")
    progress = fields.String()
    data = fields.Raw()
    _return_value = fields.Raw(data_key="output")
    _request_time = fields.String(data_key="timeRequested")
    _end_time = fields.String(data_key="timeCompleted")
    log = fields.List(fields.Dict())

    href = fields.String()

    @pre_dump
    def generate_links(self, data, **kwargs):
        try:
            url = url_for(TASK_ENDPOINT, task_id=data.id, _external=True)
        except BuildError:
            url = None
        data.href = url
        return data


class ExtensionSchema(Schema):
    name = fields.String(data_key="title")
    _name_python_safe = fields.String(data_key="pythonName")
    _cls = fields.String(data_key="pythonObject")
    meta = fields.Dict()
    description = fields.String()

    links = fields.Dict()

    @pre_dump
    def generate_links(self, data, **kwargs):
        d = {}
        for view_id, view_data in data.views.items():
            view_cls = view_data["view"]
            view_rule = view_data["rule"]
            # Try to build a URL
            try:
                url = url_for(EXTENSION_LIST_ENDPOINT, _external=True) + view_rule
            except BuildError:
                url = None
            # Make links dictionary if it doesn't yet exist
            d[view_id] = {"href": url, **description_from_view(view_cls)}

        data.links = d

        return data
