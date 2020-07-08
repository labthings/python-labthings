from apispec import APISpec
from ..json.paths import rule_to_path, rule_to_params
from .utilities import convert_to_schema_or_json

from ..utilities import get_docstring, get_summary

from flask.views import http_method_funcs
from werkzeug.routing import Rule
from http import HTTPStatus


def rule_to_apispec_path(rule: Rule, view, apispec: APISpec):
    """Generate APISpec Path arguments from a flask Rule and View

    Args:
        rule (Rule): Flask Rule for path
        view: View class
        apispec (APISpec): APISpec object to generate arguments for

    Returns:
        dict: APISpec `path` funtion argument dictionary
    """

    params = {
        "path": rule_to_path(rule),
        "operations": view.get_apispec(),
    }

    # Add URL arguments to operations
    if rule.arguments:
        for op in ("get", "post", "put", "delete"):
            if hasattr(view, op):
                params["operations"][op].update({"parameters": rule_to_params(rule)})

    return params
