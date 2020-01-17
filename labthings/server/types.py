# Marshmallow fields to JSON schema types
# Note: We shouldn't ever need to use this directly. We should go via the apispec converter
from apispec.ext.marshmallow.field_converter import DEFAULT_FIELD_MAPPING

from . import fields

# Extra standard library Python types
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple, Union
from uuid import UUID

"""
TODO: Use this to convert arbitrary dictionary into its own schema, for W3C TD

First: Convert Python non-builtins to builtins using DEFAULT_BUILTIN_CONVERSIONS
Then match types of each element to Field using DEFAULT_TYPE_MAPPING
Finally convert Fields to JSON using converter (preferred due to extra metadata), or DEFAULT_FIELD_MAPPING
"""
# Python types to Marshmallow fields
DEFAULT_TYPE_MAPPING = {
    bool: fields.Boolean,
    date: fields.Date,
    datetime: fields.DateTime,
    Decimal: fields.Decimal,
    float: fields.Float,
    int: fields.Integer,
    str: fields.String,
    time: fields.Time,
    timedelta: fields.TimeDelta,
    UUID: fields.UUID,
    dict: fields.Dict,
    Dict: fields.Dict,
}

# Functions to handle conversion of common Python types into serialisable Python types


def ndarray_to_list(o):
    return o.tolist()


def to_int(o):
    return int(o)


def to_float(o):
    return float(o)


def to_string(o):
    return str(o)


# Map of Python type conversions
DEFAULT_BUILTIN_CONVERSIONS = {
    "numpy.ndarray": ndarray_to_list,
    "numpy.int": to_int,
    "fractions.Fraction": to_float,
}

# TODO: Deserialiser with inverse defaults
# TODO: Option to switch to .npy serialisation/deserialisation (or look for a better common array format)

# Use with [x.__module__+"."+x.__name__ for x in inspect.getmro(type(POSSIBLE_MATCHER))]
# Resulting array will contain strings with the same format as keys in DEFAULT_BUILTIN_CONVERSIONS
