# Marshmallow fields to JSON schema types
# Note: We shouldn't ever need to use this directly. We should go via the apispec converter
from apispec.ext.marshmallow.field_converter import DEFAULT_FIELD_MAPPING

from labthings.server import fields
from labthings.core.utilities import rapply

from labthings.server.schema import Schema

# Extra standard library Python types
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple, Union
from uuid import UUID

import logging
import inspect
import copy

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


def make_primative(value):
    global DEFAULT_BUILTIN_CONVERSIONS, DEFAULT_TYPE_MAPPING

    logging.debug(f"Converting {value} to primative type...")
    value_typestrings = [
        x.__module__ + "." + x.__name__ for x in inspect.getmro(type(value))
    ]

    for typestring in value_typestrings:
        if typestring in DEFAULT_BUILTIN_CONVERSIONS:
            value = DEFAULT_BUILTIN_CONVERSIONS.get(typestring)(value)
            break

    # If the final type is not primative
    if not type(value) in DEFAULT_TYPE_MAPPING:
        # Fall back to a string representation
        value = str(value)

    return value


def value_to_field(value):
    global DEFAULT_TYPE_MAPPING

    if isinstance(value, (List, Tuple)) or type(value) is type(Union):
        # Get type of elements from the zeroth element.
        # NOTE: This is definitely not ideal, but we can TODO later
        element_field = value_to_field(value[0])
        return fields.List(element_field, example=value)
    if type(value) in DEFAULT_TYPE_MAPPING:
        return DEFAULT_TYPE_MAPPING.get(type(value))(example=value)
    else:
        raise TypeError(f"Unsupported data type {type(value)}")


def data_dict_to_schema(data_dict):
    working_dict = copy.deepcopy(data_dict)

    working_dict = rapply(working_dict, make_primative)
    working_dict = rapply(working_dict, value_to_field, apply_to_iterables=False)

    return working_dict


# TODO: Deserialiser with inverse defaults
# TODO: Option to switch to .npy serialisation/deserialisation (or look for a better common array format)

"""
# TODO: MOVE TO UNIT TESTS
from fractions import Fraction

d = {
    "val1": Fraction(5,2),
    "map1": {
        "subval1": "Hello",
        "subval2": False
    },
    "val2": 5
    "val3": [1, 2, 3, 4]
    "val4": range(1, 5)
}

"""
