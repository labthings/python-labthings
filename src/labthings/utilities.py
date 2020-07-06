from werkzeug.http import HTTP_STATUS_CODES
from flask import current_app

import collections.abc
import re
import operator
import sys
import os
import copy
import typing
from functools import reduce

PY3 = sys.version_info > (3,)

http_method_funcs = [
    "get",
    "post",
    "put",
    "delete",
    "patch",
    "head",
    "options",
    "trace",
]


def http_status_message(code):
    """Maps an HTTP status code to the textual status"""
    return HTTP_STATUS_CODES.get(code, "")


def description_from_view(view_class):
    """Create a dictionary description of a Flask View
    
    Args:
        view_class (View): Flask View class
    
    Returns:
        dict: Basic metadata such as description and methods from View class
    """
    summary = get_summary(view_class)

    methods = []
    for method_key in http_method_funcs:
        if hasattr(view_class, method_key):
            methods.append(method_key.upper())

            # If no class summary was given, try using summaries from method functions
            if not summary:
                summary = get_summary(getattr(view_class, method_key))

    d = {"methods": methods, "description": summary}

    return d


def view_class_from_endpoint(endpoint: str):
    """Retrieve a Flask view class from a given endpoint
    
    Args:
        endpoint (str): Endpoint corresponding to View class
    
    Returns:
        View: View class attached to the specified endpoint
    """
    return getattr(current_app.view_functions.get(endpoint), "view_class", None)


def unpack(value):
    """Return a three tuple of data, code, and headers"""
    if not isinstance(value, tuple):
        return value, 200, {}

    try:
        data, code, headers = value
        return data, code, headers
    except ValueError:
        pass

    try:
        data, code = value
        return data, code, {}
    except ValueError:
        pass

    return value, 200, {}


def clean_url_string(url: str):
    if not url:
        return "/"
    if url[0] != "/":
        return "/" + url
    else:
        return url


def get_docstring(obj, remove_newlines=True):
    """Return the docstring of an object

    Args:
        obj: Any Python object
        remove_newlines (bool): Remove newlines from the docstring (default: {True})

    Returns:
        str: Object docstring
    """
    ds = obj.__doc__
    if ds:
        stripped = [line.strip() for line in ds.splitlines() if line]
        if not remove_newlines:
            return "\n".join(stripped)
        return " ".join(stripped).replace("\n", " ").replace("\r", "")
    return ""


def get_summary(obj):
    """Return the first line of the dosctring of an object

    Args:
        obj: Any Python object

    Returns:
        str: First line of object docstring
    """
    return get_docstring(obj, remove_newlines=False).partition("\n")[0].strip()


def merge(first: dict, second: dict):
    """Recursively update a dictionary

    This will take an "update_dictionary",
    and recursively merge it with "destination_dict".

    Args:
        first (dict): Original dictionary
        second (dict): New data dictionary

    Returns:
        dict: Merged dictionary
    """
    destination_dict = copy.deepcopy(first)
    for k, v in second.items():
        # Merge lists if they're present in both objects
        if isinstance(v, list):
            # If key is missing from destination, create the list
            if k not in destination_dict:
                destination_dict[k] = []
            # If destination value is also a list, merge
            if isinstance(destination_dict[k], list):
                destination_dict[k].extend(v)
            # If destination exists but isn't a list, replace
            else:
                destination_dict[k] = v
        # Recursively merge dictionaries if the element is a dictionary
        elif isinstance(v, collections.abc.Mapping):
            if k not in destination_dict:
                destination_dict[k] = {}
            destination_dict[k] = merge(destination_dict.get(k, {}), v)
        # If not a list or dictionary, overwrite old value with new value
        else:
            destination_dict[k] = v
    return destination_dict


def rapply(data, func, *args, apply_to_iterables=True, **kwargs):
    """
    Recursively apply a function to a dictionary, list, array, or tuple

    Args:
        data: Input iterable data
        func: Function to apply to all non-iterable values
        apply_to_iterables (bool): Apply the function to elements in lists/tuples

    Returns:
        dict: Updated dictionary
    """

    # If the object is a dictionary
    if isinstance(data, collections.abc.Mapping):
        return {
            key: rapply(
                val, func, *args, apply_to_iterables=apply_to_iterables, **kwargs
            )
            for key, val in data.items()
        }
    # If the object is a list, tuple, or range
    elif apply_to_iterables and (
        isinstance(data, typing.List)
        or isinstance(data, typing.Tuple)
        or isinstance(data, range)
    ):
        return [
            rapply(x, func, *args, apply_to_iterables=apply_to_iterables, **kwargs)
            for x in data
        ]
    # if the object is neither a map nor iterable
    else:
        return func(data, *args, **kwargs)


def get_by_path(root, items):
    """Access a nested object in root by item sequence."""
    return reduce(operator.getitem, items, root)


def set_by_path(root, items, value):
    """Set a value in a nested object in root by item sequence."""
    get_by_path(root, items[:-1])[items[-1]] = value


def create_from_path(items):
    """Create a dictionary from a list of nested keys.RuntimeError

    E.g. ["foo", "bar", "baz"] will become
    {
        "foo": {
            "bar": {
                "baz": {}
            }
        }
    }

    Args:
        items (list): Key path

    Returns:
        dict: Nested dictionary of key path
    """
    tree_dict = {}
    for key in reversed(items):
        tree_dict = {key: tree_dict}
    return tree_dict


def camel_to_snake(name):
    """Convert a CamelCase string into snake_case

    Args:
        name (str): CamelCase string

    Returns:
        str: snake_case string
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def camel_to_spine(name):
    """Convert a CamelCase string into spine-case

    Args:
        name (str): CamelCase string

    Returns:
        str: spine-case string
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1-\2", s1).lower()


def snake_to_spine(name):
    """Convert a snake_case string into spine-case

    Args:
        name (str): snake_case string

    Returns:
        str: spine-case string
    """
    return name.replace("_", "-")


def snake_to_camel(snake_str):
    """Convert a snake_case string into lowerCamelCase

    Args:
        name (str): snake_case string

    Returns:
        str: lowerCamelCase string
    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def path_relative_to(source_file, *paths):
    """Given a python module __file__, return an absolute path relative to its location
    
    Args:
        source_file: Module __file__ attribute
        paths {str} -- Paths to add to source file location
    """
    return os.path.join(os.path.abspath(os.path.dirname(source_file)), *paths)
