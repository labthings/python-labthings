import collections.abc
import re
import base64
import operator
import sys
from functools import reduce

try:
    from collections.abc import OrderedDict
except ImportError:
    from collections import OrderedDict

PY3 = sys.version_info > (3,)


def get_docstring(obj):
    ds = obj.__doc__
    if ds:
        return ds.strip()
    else:
        return ""


def get_summary(obj):
    return get_docstring(obj).partition("\n")[0].strip()


def rupdate(d, u):
    for k, v in u.items():
        # Merge lists if they're present in both objects
        if isinstance(v, list):
            if not k in d:
                d[k] = []
            if isinstance(d[k], list):
                d[k].extend(v)
        # Recursively merge dictionaries if the element is a dictionary
        elif isinstance(v, collections.abc.Mapping):
            if not k in d:
                d[k] = {}
            d[k] = rupdate(d.get(k, {}), v)
        # If not a list or dictionary, overwrite old value with new value
        else:
            d[k] = v
    return d


def rapply(data, func):
    """
    Recursively apply a function to a dictionary, list, array, or tuple

    Args:
        data: Input iterable data
        func: Function to apply to all non-iterable values
    """
    # If the object is a dictionary
    if isinstance(data, collections.abc.Mapping):
        return {key: rapply(val, func) for key, val in data.items()}
    # If the object is iterable but NOT a dictionary or a string
    elif (
        isinstance(data, collections.abc.Iterable)
        and not isinstance(data, collections.abc.Mapping)
        and not isinstance(data, str)
    ):
        return [rapply(x, func) for x in data]
    # if the object is neither a map nor iterable
    else:
        return func(data)


def get_by_path(root, items):
    """Access a nested object in root by item sequence."""
    return reduce(operator.getitem, items, root)


def set_by_path(root, items, value):
    """Set a value in a nested object in root by item sequence."""
    get_by_path(root, items[:-1])[items[-1]] = value


def create_from_path(items):
    tree_dict = {}
    for key in reversed(items):
        tree_dict = {key: tree_dict}
    return tree_dict


def bottom_level_name(obj):
    return obj.__name__.split(".")[-1]


def camel_to_snake(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def camel_to_spine(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1-\2", s1).lower()


def snake_to_spine(name):
    return name.replace("_", "-")
