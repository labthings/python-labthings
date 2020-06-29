from apispec import APISpec
from .paths import rule_to_path, rule_to_params
from .utilities import convert_to_schema_or_json

from ..schema import Schema

from labthings.core.utilities import get_docstring, get_summary

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

            ops[op] = {
                "description": getattr(view, "description", None)
                or get_docstring(view),
                "summary": getattr(view, "summary", None) or get_summary(view),
                "tags": list(view.get_tags()),
            }

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

                for code, response in view.get_responses().items():
                    ops[op]["responses"][code] = {
                        "description": response.get("description")
                        or HTTPStatus(code).phrase,
                        "content": {
                            # See if response description specifies a content_type
                            # If not, assume application/json
                            response.get("content_type", "application/json"): {
                                "schema": convert_to_schema_or_json(
                                    response.get("schema"), apispec
                                )
                            }
                            if response.get("schema")
                            else {}  # If no schema is defined, don't include one in the APISpec
                        },
                    }
            else:
                # If no explicit responses are known, populate with defaults
                ops[op]["responses"] = {200: {HTTPStatus(200).phrase}}

    return ops
