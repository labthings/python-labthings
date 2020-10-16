# Marshmallow fields
from base64 import b64decode

from marshmallow import ValidationError
from marshmallow.fields import (
    URL,
    UUID,
    AwareDateTime,
    Bool,
    Boolean,
    Constant,
    Date,
    DateTime,
    Decimal,
    Dict,
    Email,
    Field,
    Float,
    Function,
    Int,
    Integer,
    List,
    Mapping,
    Method,
    NaiveDateTime,
    Nested,
    Number,
    Pluck,
    Raw,
    Str,
    String,
    Time,
    TimeDelta,
    Tuple,
    Url,
)

__all__ = [
    "Bytes",
    "Field",
    "Raw",
    "Nested",
    "Mapping",
    "Dict",
    "List",
    "Tuple",
    "String",
    "UUID",
    "Number",
    "Integer",
    "Decimal",
    "Boolean",
    "Float",
    "DateTime",
    "NaiveDateTime",
    "AwareDateTime",
    "Time",
    "Date",
    "TimeDelta",
    "Url",
    "URL",
    "Email",
    "Method",
    "Function",
    "Str",
    "Bool",
    "Int",
    "Constant",
    "Pluck",
]


class Bytes(Field):
    """
    Marshmallow field for `bytes` objects
    """

    def _jsonschema_type_mapping(self):
        """ """
        return {"type": "string", "contentEncoding": "base64"}

    def _validate(self, value):
        """

        :param value:

        """
        if not isinstance(value, bytes):
            raise ValidationError("Invalid input type.")

        if value is None or value == b"":
            raise ValidationError("Invalid value")

    def _deserialize(self, value, attr, data, **kwargs):
        """

        :param value:
        :param attr:
        :param data:
        :param **kwargs:

        """
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return b64decode(value)
        else:
            raise self.make_error("invalid", input=value)
