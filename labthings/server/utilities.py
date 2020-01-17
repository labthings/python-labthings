from ..core.utilities import (
    get_docstring,
    get_summary,
)

from .view import View

from flask import current_app


def description_from_view(view_class):
    summary = get_summary(view_class)

    methods = []
    for method_key in View.methods:
        if hasattr(view_class, method_key):
            methods.append(method_key.upper())

            # If no class summary was given, try using summaries from method functions
            if not summary:
                summary = get_summary(getattr(view_class, method_key))

    d = {"methods": methods, "description": summary}

    return d


def view_class_from_endpoint(endpoint: str):
    return current_app.view_functions[endpoint].view_class
