from labthings.core.utilities import get_summary

from werkzeug.http import HTTP_STATUS_CODES
from flask import current_app


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
