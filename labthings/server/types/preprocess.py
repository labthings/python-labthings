# Functions to handle conversion of common Python types into serialisable Python types
from apispec.ext.marshmallow.field_converter import DEFAULT_FIELD_MAPPING
import inspect

from .registry import TypeRegistry


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
    # FIXME: Better handling of type registries
    _primitives = TypeRegistry()._registry.keys()

    value_typestrings = [
        x.__module__ + "." + x.__name__ for x in inspect.getmro(type(value))
    ]

    for typestring in value_typestrings:
        if typestring in DEFAULT_BUILTIN_CONVERSIONS:
            value = DEFAULT_BUILTIN_CONVERSIONS.get(typestring)(value)
            break

    # If the final type is not primitive
    if not type(value) in _primitives:
        # Fall back to a string representation
        value = str(value)

    return value


# TODO: Deserialiser with inverse defaults
# TODO: Option to switch to .npy serialisation/deserialisation (see OFM server)
