from apispec import APISpec
from .paths import rule_to_path, rule_to_params
from .utilities import convert_to_schema_or_json

from ..schema import Schema

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
        "operations": view_to_apispec_operations(view, apispec),
        **getattr(view, "docs", {}),
    }

    # Add URL arguments to operations
    if rule.arguments:
        for op in ("get", "post", "put", "delete"):
            if hasattr(view, op):
                params["operations"][op].update({"parameters": rule_to_params(rule)})

    return params


def view_to_apispec_operations(view, apispec: APISpec):
    """Generate APISpec `operations` argument from a flask View"""

    # Build dictionary of operations (HTTP methods)
    ops = {}
    for op in ("get", "post", "put", "delete"):
        if hasattr(view, op):

            ops[op] = {}

            # Add arguments schema
            if (op in (("post", "put", "delete"))) and hasattr(view, "get_args"):
                request_schema = convert_to_schema_or_json(view.get_args(), apispec)
                if request_schema:
                    ops[op]["requestBody"] = {
                        "content": {"application/json": {"schema": request_schema}}
                    }

            # Add response schema
            if hasattr(view, "get_responses"):
                ops[op]["responses"] = {}

                print(view.get_responses())
                for code, schema in view.get_responses().items():
                    ops[op]["responses"][code] = {
                        "description": HTTPStatus(code).phrase,
                        "content": {
                            getattr(view, "content_type", "application/json"): {
                                "schema": convert_to_schema_or_json(schema, apispec)
                                or Schema()
                            }
                        },
                    }
            else:
                # If no explicit responses are known, populate with defaults
                ops[op]["responses"] = {200: {HTTPStatus(200).phrase}}

    return ops
