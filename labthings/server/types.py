# Marshmallow fields to JSON schema types
# Note: We shouldn't ever need to use this directly.
# We should go via the apispec converter
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
    """Convert a Numpy ndarray into a list of values
    
    Args:
        o (numpy.ndarray): Data to convert
    
    Returns:
        list: Python list of data
    """
    return o.tolist()


def to_int(o):
    """Convert a value into a Python integer
    
    Args:
        o: Data to convert
    
    Returns:
        int: Python int of data
    """
    return int(o)


def to_float(o):
    """Convert a value into a Python float
    
    Args:
        o: Data to convert
    
    Returns:
        int: Python float of data
    """
    return float(o)


def to_string(o):
    """Convert a value into a Python string
    
    Args:
        o: Data to convert
    
    Returns:
        int: Python string of data
    """
    return str(o)


# Map of Python type conversions
DEFAULT_BUILTIN_CONVERSIONS = {
    "numpy.ndarray": ndarray_to_list,
    "numpy.int": to_int,
    "fractions.Fraction": to_float,
}


def make_primitive(value):
    """Attempt to convert a value into a primitive Python type
    
    Args:
        value: Data to convert
    
    Returns:
        Converted data if possible, otherwise original data
    """
    global DEFAULT_BUILTIN_CONVERSIONS, DEFAULT_TYPE_MAPPING

    logging.debug(f"Converting {value} to primitive type...")
    value_typestrings = [
        x.__module__ + "." + x.__name__ for x in inspect.getmro(type(value))
    ]

    for typestring in value_typestrings:
        if typestring in DEFAULT_BUILTIN_CONVERSIONS:
            value = DEFAULT_BUILTIN_CONVERSIONS.get(typestring)(value)
            break

    # If the final type is not primitive
    if not type(value) in DEFAULT_TYPE_MAPPING:
        # Fall back to a string representation
        value = str(value)

    return value


def value_to_field(value):
    """Attempt to match a value to a Marshmallow field type
    
    Args:
        value: Data to obtain field from
    
    Raises:
        TypeError: Data is not of a type that maps to a Marshmallow field
    
    Returns:
        Marshmallow field best matching the value type
    """
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


def data_dict_to_schema(data_dict: dict):
    """Attempt to create a Marshmallow schema from a dictionary of data
    
    Args:
        data_dict (dict): Dictionary of data
    
    Returns:
        dict: Dictionary of Marshmallow fields matching input data types
    """
    working_dict = copy.deepcopy(data_dict)

    working_dict = rapply(working_dict, make_primitive)
    working_dict = rapply(working_dict, value_to_field, apply_to_iterables=False)

    return working_dict


# TODO: Deserialiser with inverse defaults
# TODO: Option to switch to .npy serialisation/deserialisation (see OFM server)
