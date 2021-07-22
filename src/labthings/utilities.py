import copy
import inspect
import operator
import os
import re
import sys
import time
from collections import UserString
from functools import reduce
from typing import Any, Callable, Dict, List, Tuple, Type, Union

from flask import current_app, has_request_context, request
from werkzeug.http import HTTP_STATUS_CODES

PY3 = sys.version_info > (3,)


class TimeoutTracker:
    """ """

    def __init__(self, timeout: int):
        self.timeout_time = time.time() + timeout

    @property
    def stopped(self):
        """ """
        return time.time() >= self.timeout_time


class ResourceURL(UserString):
    """
    Takes a URL path relative to the host_url (e.g. /api/myresource),
    and optionally prepends the host URL to generate a complete URL
    (e.g. http://localhost:7485/api/myresource).
    Behaves as a Python string.
    """

    def __init__(self, path: str, external: bool = True, protocol: str = ""):
        self.path = path
        self.external = external
        # Strip :// if the user mistakenly included it in the argument
        self.protocol = protocol.rstrip("://")
        UserString.__init__(self, path)

    @property  # type: ignore
    def data(self) -> str:  # type: ignore
        if self.external and has_request_context():
            prefix = request.host_url.rstrip("/")
            # Optional protocol override
            if self.protocol:
                # Strip old protocol and replace with custom protocol
                prefix = self.protocol + "://" + prefix.split("://")[1]
        else:
            prefix = ""
        return prefix + self.path

    @data.setter
    def data(self, path: str):
        self.path = path


def http_status_message(code: int) -> str:
    """Maps an HTTP status code to the textual status

    :param code:

    """
    return HTTP_STATUS_CODES.get(code, "")


def description_from_view(view_class: Type) -> dict:
    """Create a dictionary description of a Flask View

    :param view_class: Flask View class
    :type view_class: View
    :returns: Basic metadata such as description and methods from View class
    :rtype: dict

    """
    summary = get_summary(view_class)

    methods = []
    for method_key in ("get", "post", "put"):
        if hasattr(view_class, method_key):
            methods.append(method_key.upper())

            # If no class summary was given, try using summaries from method functions
            if not summary:
                summary = get_summary(getattr(view_class, method_key))

    d = {"methods": methods, "description": summary}

    return d


def view_class_from_endpoint(endpoint: str) -> Type:
    """Retrieve a Flask view class from a given endpoint

    :param endpoint: Endpoint corresponding to View class
    :type endpoint: str
    :param endpoint: str:
    :returns: View class attached to the specified endpoint
    :rtype: View

    """
    return getattr(current_app.view_functions.get(endpoint), "view_class", None)


def unpack(value: Any) -> Tuple:
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


def clean_url_string(url: str) -> str:
    """

    :param url: str:

    """
    if not url:
        return "/"
    if url[0] != "/":
        return "/" + url
    else:
        return url


def get_docstring(obj: Any, remove_newlines=True, remove_summary=False) -> str:
    """Return the docstring of an object

    If `remove_newlines` is `True` (default), newlines are removed from the string.
    If `remove_summary` is `True` (not default), and the docstring's second line
    is blank, the first two lines are removed.  If the docstring follows the
    convention of a one-line summary, a blank line, and a description, this will
    get just the description.

    If `remove_newlines` is `False`, the docstring is processed by
    `inspect.cleandoc()` to remove whitespace from the start of each line.

    :param obj: Any Python object
    :param remove_newlines: bool (Default value = True)
    :param remove_summary: bool (Default value = False)
    :returns: str: Object docstring

    """
    ds = obj.__doc__
    if not ds:
        return ""
    if remove_summary:
        lines = ds.splitlines()
        if len(lines) > 2 and lines[1].strip() == "":
            ds = "\n".join(lines[2:])
    if remove_newlines:
        stripped = [line.strip() for line in ds.splitlines() if line]
        return " ".join(stripped).replace("\n", " ").replace("\r", "")
    return inspect.cleandoc(ds)  # Strip spurious indentation/newlines


def get_summary(obj: Any) -> str:
    """Return the first line of the dosctring of an object

    :param obj: Any Python object
    :returns: str: First line of object docstring

    """
    return get_docstring(obj, remove_newlines=False).partition("\n")[0].strip()


def merge(first: dict, second: dict) -> dict:
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
        elif isinstance(v, dict):
            if k not in destination_dict:
                destination_dict[k] = {}
            destination_dict[k] = merge(destination_dict.get(k, {}), v)
        # If not a list or dictionary, overwrite old value with new value
        else:
            destination_dict[k] = v
    return destination_dict


def rapply(
    data: Any, func: Callable, *args, apply_to_iterables: bool = True, **kwargs
) -> Union[Dict, List]:
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
    if isinstance(data, dict):
        return {
            key: rapply(
                val, func, *args, apply_to_iterables=apply_to_iterables, **kwargs
            )
            for key, val in data.items()
        }
    # If the object is a list, tuple, or range
    elif apply_to_iterables and (isinstance(data, (list, tuple, range))):
        return [
            rapply(x, func, *args, apply_to_iterables=apply_to_iterables, **kwargs)
            for x in data
        ]
    # if the object is neither a map nor iterable
    else:
        return func(data, *args, **kwargs)


def get_by_path(root: Dict[Any, Any], items: List[Any]) -> Any:
    """Access a nested object in root by item sequence.

    :param root:
    :param items:

    """
    return reduce(operator.getitem, items, root)


def set_by_path(root: Dict[Any, Any], items: List[Any], value: Any):
    """Set a value in a nested object in root by item sequence.

    :param root:
    :param items:
    :param value:

    """
    get_by_path(root, items[:-1])[items[-1]] = value


def create_from_path(items: List[Any]) -> dict:
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
    tree_dict: Dict[Any, Any] = {}
    for key in reversed(items):
        tree_dict = {key: tree_dict}
    return tree_dict


def camel_to_snake(name: str) -> str:
    """Convert a CamelCase string into snake_case

    :param name: CamelCase string
    :type name: str
    :returns: snake_case string
    :rtype: str

    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def camel_to_spine(name: str) -> str:
    """Convert a CamelCase string into spine-case

    :param name: CamelCase string
    :type name: str
    :returns: spine-case string
    :rtype: str

    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1-\2", s1).lower()


def snake_to_spine(name: str) -> str:
    """Convert a snake_case string into spine-case

    :param name: snake_case string
    :type name: str
    :returns: spine-case string
    :rtype: str

    """
    return name.replace("_", "-")


def snake_to_camel(snake_str: str) -> str:
    """Convert a snake_case string into lowerCamelCase

    :param name: snake_case string
    :type name: str
    :param snake_str:
    :returns: lowerCamelCase string
    :rtype: str

    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def path_relative_to(source_file: str, *paths: str):
    """Given a python module __file__, return an absolute path relative to its location

    :param source_file: Module __file__ attribute
    :param source_file: Module __file__ attribute
        paths {str} -- Paths to add to source file location
    :param *paths:

    """
    return os.path.join(os.path.abspath(os.path.dirname(source_file)), *paths)
