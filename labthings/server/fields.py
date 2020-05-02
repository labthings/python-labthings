# Marshmallow fields
from marshmallow import ValidationError
from marshmallow.fields import (
    Field,
    Raw,
    Nested,
    Mapping,
    Dict,
    List,
    Tuple,
    String,
    UUID,
    Number,
    Integer,
    Decimal,
    Boolean,
    Float,
    DateTime,
    NaiveDateTime,
    AwareDateTime,
    Time,
    Date,
    TimeDelta,
    Url,
    URL,
    Email,
    Method,
    Function,
    Str,
    Bool,
    Int,
    Constant,
    Pluck,
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
    def _validate(self, value):
        if not isinstance(value, bytes):
            raise ValidationError("Invalid input type.")

        if value is None or value == b"":
            raise ValidationError("Invalid value")
