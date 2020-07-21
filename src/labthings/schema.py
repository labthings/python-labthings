# -*- coding: utf-8 -*-
from flask import url_for
from werkzeug.routing import BuildError
from marshmallow import Schema, pre_load, pre_dump, validate
from collections.abc import Mapping

from .names import ACTION_ENDPOINT, TASK_ENDPOINT, EXTENSION_LIST_ENDPOINT
from .utilities import view_class_from_endpoint, description_from_view
from . import fields

__all__ = [
    "Schema",
    "pre_load",
    "pre_dump",
    "validate",
]


class FieldSchema(Schema):
    """"Virtual schema" for handling individual fields treated as schemas.
    
    For example, when serializing/deserializing individual values that are not
    attributes of an object, like passing a single number as the request/response body


    """

    def __init__(self, field: fields.Field):
        """Create a converter for data of the field type

        Args:
            field (Field): Marshmallow Field type of data
        """
        Schema.__init__(self)
        self.field = field

    def deserialize(self, value):
        """

        :param value: 

        """
        return self.field.deserialize(value)

    def serialize(self, value):
        """Serialize a value to Field type

        :param value: Data to serialize
        :returns: Serialized data

        """
        obj = type("obj", (object,), {"value": value})

        return self.field.serialize("value", obj)

    def dump(self, value):
        """

        :param value: 

        """
        return self.serialize(value)


class TaskSchema(Schema):
    """Legacy schema for background actions. Will eventually be replaced by ActionSchema,"""

    _ID = fields.String(data_key="id")
    target_string = fields.String(data_key="function")
    _status = fields.String(data_key="status")
    progress = fields.String()
    data = fields.Raw()
    _return_value = fields.Raw(data_key="return")
    _start_time = fields.DateTime(data_key="start_time")
    _end_time = fields.DateTime(data_key="end_time")
    log = fields.List(fields.Dict())

    links = fields.Dict()

    @pre_dump
    def generate_links(self, data, **kwargs):
        """

        :param data: 
        :param **kwargs: 

        """
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
    """ """
    _ID = fields.String(data_key="id")
    _status = fields.String(data_key="status")
    progress = fields.String()
    data = fields.Raw()
    # _return_value = fields.Raw(data_key="output")
    _request_time = fields.DateTime(data_key="timeRequested")
    _end_time = fields.DateTime(data_key="timeCompleted")
    # TODO: Make a proper log schema
    log = fields.List(fields.Dict())

    # Dump unformatted input and output
    # Function-level marshal_with will handle formatting
    output = fields.Field()
    input = fields.Field()

    href = fields.String()
    links = fields.Dict()

    @pre_dump
    def generate_links(self, data, **kwargs):
        """

        :param data: 
        :param **kwargs: 

        """
        # Add Mozilla format href
        try:
            url = url_for(ACTION_ENDPOINT, task_id=data.id, _external=True)
        except BuildError:
            url = None
        data.href = url

        # Add full link description
        data.links = {
            "self": {
                "href": url,
                "mimetype": "application/json",
                **description_from_view(view_class_from_endpoint(ACTION_ENDPOINT)),
            }
        }

        return data


def build_action_schema(output_schema: Schema, input_schema: Schema, name: str = None):
    """Builds a complete schema for a given ActionView. That is, it reads any input and output
    schemas attached to the POST method, and nests them within the input/output fields of
    the generic ActionSchema.
    NOTE: This is only for documentation purposes. When Action responses are built by the
    HTTP server, the generic ActionSchema will be used for marshaling. This is because the
    post() functions return value will already be marshaled because of its @marshal_with
    decorator, and thus will already be a formatted dictionary object.

    :param output_schema: Schema: 
    :param input_schema: Schema: 
    :param name: str:  (Default value = None)

    """
    # Create a name for the generated schema
    if not name:
        name = str(id(output_schema))
    if not name.endswith("Action"):
        name = f"{name}Action"

    class_attrs = {"output": None, "input": None}

    for key, schema in {"output": output_schema, "input": input_schema}.items():

        # If a real schema, nest it
        if isinstance(schema, Schema):
            class_attrs[key] = fields.Nested(schema)
        # If a dictionary schema, build a real schema then nest it
        elif isinstance(schema, Mapping):
            class_attrs[key] = fields.Nested(Schema.from_dict(schema))
        # If a single field, set it as the output Field, and override its data_key
        elif isinstance(schema, fields.Field):
            class_attrs[key] = schema
        # Otherwise allow any
        elif schema is None:
            class_attrs[key] = fields.Raw()
        else:
            raise TypeError(
                f"Unsupported schema type {schema}. "
                "Ensure schema is a Schema object, Field object, "
                "or dictionary of Field objects"
            )

    # Build a Schema class for the Action
    return type(name, (ActionSchema,), class_attrs)


class ExtensionSchema(Schema):
    """ """
    name = fields.String(data_key="title")
    _name_python_safe = fields.String(data_key="pythonName")
    _cls = fields.String(data_key="pythonObject")
    meta = fields.Dict()
    description = fields.String()

    links = fields.Dict()

    @pre_dump
    def generate_links(self, data, **kwargs):
        """

        :param data: 
        :param **kwargs: 

        """
        d = {}
        for view_id, view_data in data.views.items():
            view_cls = view_data.get("view")
            view_urls = view_data.get("urls")
            # Try to build a URL
            try:
                urls = [
                    url_for(EXTENSION_LIST_ENDPOINT, _external=True) + url
                    for url in view_urls
                ]
            except BuildError:
                urls = []
            # TODO: Tidy up this nasty jazz
            if len(urls) == 0:
                urls = None
            elif len(urls) == 1:
                urls = urls[0]
            # Make links dictionary if it doesn't yet exist
            d[view_id] = {"href": urls, **description_from_view(view_cls)}

        data.links = d

        return data
