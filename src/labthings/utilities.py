from werkzeug.http import HTTP_STATUS_CODES
from flask import current_app

import collections.abc
import re
import operator
import sys
import os
import copy
import time
import typing
import inspect
from functools import reduce
from typing import Callable

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


class TimeoutTracker:
    """ """

    def __init__(self, timeout: int):
        self.timeout_time = time.time() + timeout

    @property
    def stopped(self):
        """ """
        return time.time() >= self.timeout_time


def http_status_message(code):
    """Maps an HTTP status code to the textual status

    :param code: 

    """
    return HTTP_STATUS_CODES.get(code, "")


def description_from_view(view_class):
    """Create a dictionary description of a Flask View

    :param view_class: Flask View class
    :type view_class: View
    :returns: Basic metadata such as description and methods from View class
    :rtype: dict

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

    :param endpoint: Endpoint corresponding to View class
    :type endpoint: str
    :param endpoint: str: 
    :returns: View class attached to the specified endpoint
    :rtype: View

    """
    return getattr(current_app.view_functions.get(endpoint), "view_class", None)


def unpack(value):
    """

    :param value: 

    """
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
    """

    :param url: str: 

    """
    if not url:
        return "/"
    if url[0] != "/":
        return "/" + url
    else:
        return url


def get_docstring(obj, remove_newlines=True):
    """Return the docstring of an object

    :param obj: Any Python object
    :param remove_newlines: bool (Default value = True)
    :returns: str: Object docstring

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

    :param obj: Any Python object
    :returns: str: First line of object docstring

    """
    return get_docstring(obj, remove_newlines=False).partition("\n")[0].strip()


def merge(first: dict, second: dict):
    """Recursively update a dictionary
    
    This will take an "update_dictionary",
    and recursively merge it with "destination_dict".

    :param first: Original dictionary
    :type first: dict
    :param second: New data dictionary
    :type second: dict
    :param first: dict: 
    :param second: dict: 
    :returns: Merged dictionary
    :rtype: dict

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
    """Recursively apply a function to a dictionary, list, array, or tuple

    :param data: Input iterable data
    :param func: Function to apply to all non-iterable values
    :param apply_to_iterables: Apply the function to elements in lists/tuples (Default value = True)
    :type apply_to_iterables: bool
    :param *args: 
    :param **kwargs: 
    :returns: Updated dictionary
    :rtype: dict

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
    """Access a nested object in root by item sequence.

    :param root: 
    :param items: 

    """
    return reduce(operator.getitem, items, root)


def set_by_path(root, items, value):
    """Set a value in a nested object in root by item sequence.

    :param root: 
    :param items: 
    :param value: 

    """
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

    :param items: Key path
    :type items: list
    :returns: Nested dictionary of key path
    :rtype: dict

    """
    tree_dict = {}
    for key in reversed(items):
        tree_dict = {key: tree_dict}
    return tree_dict


def camel_to_snake(name):
    """Convert a CamelCase string into snake_case

    :param name: CamelCase string
    :type name: str
    :returns: snake_case string
    :rtype: str

    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def camel_to_spine(name):
    """Convert a CamelCase string into spine-case

    :param name: CamelCase string
    :type name: str
    :returns: spine-case string
    :rtype: str

    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1-\2", s1).lower()


def snake_to_spine(name):
    """Convert a snake_case string into spine-case

    :param name: snake_case string
    :type name: str
    :returns: spine-case string
    :rtype: str

    """
    return name.replace("_", "-")


def snake_to_camel(snake_str):
    """Convert a snake_case string into lowerCamelCase

    :param name: snake_case string
    :type name: str
    :param snake_str: 
    :returns: lowerCamelCase string
    :rtype: str

    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def path_relative_to(source_file, *paths):
    """Given a python module __file__, return an absolute path relative to its location

    :param source_file: Module __file__ attribute
    :param source_file: Module __file__ attribute
        paths {str} -- Paths to add to source file location
    :param *paths: 

    """
    return os.path.join(os.path.abspath(os.path.dirname(source_file)), *paths)


def url_for_property(property_object: object, property_name: str):
    """

    :param property_object: object: 
    :param property_name: str: 

    """
    return f"/properties/{property_object.__class__.__name__}/{property_name}"


def url_for_action(action_object: object, action_name: str):
    """

    :param action_object: object: 
    :param action_name: str: 

    """
    return f"/actions/{action_object.__class__.__name__}/{action_name}"
