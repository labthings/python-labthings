from ..view import View
from apispec import APISpec

from ...core.utilities import get_docstring, get_summary, rupdate
from .paths import rule_to_path, rule_to_params
from .utilities import convert_schema

from werkzeug.routing import Rule
from http import HTTPStatus


def rule_to_apispec_path(rule: Rule, view: View, spec: APISpec):
    """Generate APISpec Path arguments from a flask Rule and View
    
    Args:
        rule (Rule): Flask Rule for path
        view (View): Flask View for path
        spec (APISpec): APISpec object to generate arguments for
    
    Returns:
        dict: APISpec `path` funtion argument dictionary
    """
    params = {
        "path": rule_to_path(rule),
        "operations": view_to_apispec_operations(view, spec),
        "description": get_docstring(view),
        "summary": get_summary(view),
    }

    # Add URL arguments
    if rule.arguments:
        for op in params.get("operations").keys():
            params["operations"][op].update({"parameters": rule_to_params(rule)})

    # Add extra parameters
    if hasattr(view, "__apispec__"):
        # Recursively update params
        rupdate(params, view.__apispec__)

    return params


def view_to_apispec_operations(view: View, spec: APISpec):
    """Generate APISpec `operations` argument from a flask View
    
    Args:
        view (View): Flask View for operations
        spec (APISpec): APISpec object to generate arguments for
    
    Returns:
        dict: APISpec `operations` dictionary
    """
    # Operations inherit tags from parent
    inherited_tags = []
    if hasattr(view, "__apispec__"):
        inherited_tags = getattr(view, "__apispec__").get("tags", [])

    # Build dictionary of operations (HTTP methods)
    ops = {}
    for method in View.methods:
        if hasattr(view, method):
            ops[method] = {}

            rupdate(
                ops[method],
                {
                    "description": get_docstring(getattr(view, method)),
                    "summary": get_summary(getattr(view, method)),
                    "tags": inherited_tags,
                },
            )

            rupdate(
                ops[method], method_to_apispec_operation(getattr(view, method), spec)
            )

    return ops


def method_to_apispec_operation(method: callable, spec: APISpec):
    """Generate APISpec `operation` parameters from a flask View method
    
    Args:
        method (callable): Flask View method for APISpec operation
        spec (APISpec): APISpec object to generate arguments for
    
    Returns:
        dict: APISpec `operation` dictionary
    """
    if hasattr(method, "__apispec__"):
        apispec = getattr(method, "__apispec__")
    else:
        apispec = {}

    op = {}
    if "_params" in apispec:
        rupdate(
            op,
            {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": convert_schema(apispec.get("_params"), spec)
                        }
                    }
                }
            },
        )

    if "_schema" in apispec:
        for code, schema in apispec.get("_schema", {}).items():
            rupdate(
                op,
                {
                    "responses": {
                        code: {
                            "description": HTTPStatus(code).phrase,
                            "content": {
                                "application/json": {
                                    "schema": convert_schema(schema, spec)
                                }
                            },
                        }
                    }
                },
            )
    else:
        # If no explicit responses are known, populate with defaults
        rupdate(
            op,
            {
                "responses": {
                    200: {"description": get_summary(method) or HTTPStatus(200).phrase}
                }
            },
        )

    # Bung in any extra swagger fields supplied
    for key, val in apispec.items():
        if key not in ["_params", "_schema"]:
            rupdate(op, {key: val})

    return op
