# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union

from flask import url_for
from marshmallow import Schema, pre_dump, pre_load, validate
from werkzeug.routing import BuildError

from . import fields
from .names import ACTION_ENDPOINT, EXTENSION_LIST_ENDPOINT
from .utilities import description_from_view, view_class_from_endpoint

__all__ = ["Schema", "pre_load", "pre_dump", "validate", "FuzzySchemaType"]

# Type alias for a Schema, Field, or Dict of Fields or Types
FuzzySchemaType = Union[Schema, fields.Field, Dict[str, Union[fields.Field, type]]]


class FieldSchema(Schema):
    """ "Virtual schema" for handling individual fields treated as schemas.

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

    # We disable pylint unused-argument so we can keep the same signature as the base class
    # pylint: disable=unused-argument
    def dump(self, obj: Any, *, many: Optional[bool] = None):
        """
        :param value:
        """
        return self.serialize(obj)


class LogRecordSchema(Schema):
    name = fields.String()
    message = fields.String()
    levelname = fields.String()
    levelno = fields.Integer()
    lineno = fields.Integer()
    filename = fields.String()
    created = fields.DateTime()

    @pre_dump
    def preprocess(self, data, **_):
        if isinstance(data, logging.LogRecord):
            data.message = data.getMessage()
            if not isinstance(data.created, datetime):
                data.created = datetime.fromtimestamp(data.created)
        return data


class ActionSchema(Schema):
    """Represents a running or completed Action

    Actions can run in the background, started by one request
    and subsequently polled for updates.  This schema represents
    one Action."""

    action = fields.String()
    _ID = fields.String(data_key="id")
    _status = fields.String(
        data_key="status",
        validate=validate.OneOf(
            ["pending", "running", "completed", "cancelled", "error"]
        ),
    )
    progress = fields.Integer()
    data = fields.Raw()
    _request_time = fields.DateTime(data_key="timeRequested")
    _end_time = fields.DateTime(data_key="timeCompleted")
    log = fields.List(fields.Nested(LogRecordSchema()))

    input = fields.Raw()
    output = fields.Raw()

    href = fields.String()
    links = fields.Dict()

    @pre_dump
    def generate_links(self, data, **_):
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


def nest_if_needed(schema):
    """Convert a schema, dict, or field into a field."""
    # If we have a real schema, nest it
    if isinstance(schema, Schema):
        return fields.Nested(schema)
    # If a dictionary schema, build a real schema then nest it
    if isinstance(schema, dict):
        return fields.Nested(Schema.from_dict(schema))
    # If a single field, set it as the output Field, and override its data_key
    if isinstance(schema, fields.Field):
        return schema

    raise TypeError(
        f"Unsupported schema type {schema}. "
        "Ensure schema is a Schema object, Field object, "
        "or dictionary of Field objects"
    )


def build_action_schema(
    output_schema: Optional[FuzzySchemaType],
    input_schema: Optional[FuzzySchemaType],
    name: Optional[str] = None,
    base_class: type = ActionSchema,
):
    """Builds a complete schema for a given ActionView.

    This method combines input and output schemas for a particular
    Action with the generic ActionSchema to give a specific ActionSchema
    subclass for that Action.

    This is used in the Thing Description (where it is serialised to
    JSON in-place) but not in the OpenAPI description (where the input,
    output, and ActionSchema schemas are combined using `allOf`.)

    :param output_schema: Schema:
    :param input_schema: Schema:
    :param name: str:  (Default value = None)

    """
    # Create a name for the generated schema
    if not name:
        name = str(id(output_schema))
    if not name.endswith("Action"):
        name = f"{name}Action"

    class_attrs: Dict[str, Union[fields.Nested, fields.Field, str]] = {}

    class_attrs[
        "__doc__"
    ] = f"Description of an action, with specific parameters for `{name}`"
    if input_schema:
        class_attrs["input"] = nest_if_needed(input_schema)
    if output_schema:
        class_attrs["output"] = nest_if_needed(output_schema)

    return type(name, (base_class,), class_attrs)


class EventSchema(Schema):
    event = fields.String()
    timestamp = fields.DateTime()
    data = fields.Raw()


class ExtensionSchema(Schema):
    """ """

    name = fields.String(data_key="title")
    _name_python_safe = fields.String(data_key="pythonName")
    _cls = fields.String(data_key="pythonObject")
    meta = fields.Dict()
    description = fields.String()

    links = fields.Dict()

    @pre_dump
    def generate_links(self, data, **_):
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
            # If URL list is empty
            if len(urls) == 0:
                urls = None
            # If only 1 URL is given
            elif len(urls) == 1:
                urls = urls[0]
            # Make links dictionary if it doesn't yet exist
            d[view_id] = {"href": urls, **description_from_view(view_cls)}

        data.links = d

        return data
