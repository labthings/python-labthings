from ..view import View
from apispec import APISpec

from ...core.utilities import get_summary, merge
from .paths import rule_to_path, rule_to_params
from .utilities import convert_to_schema_or_json, update_spec

from werkzeug.routing import Rule
from http import HTTPStatus

from pprint import pprint


def rule_to_apispec_path(rule: Rule, spec_dict: dict, apispec: APISpec):
    """Generate APISpec Path arguments from a flask Rule and View
    
    Args:
        rule (Rule): Flask Rule for path
        spec_dict (dict): Compiled API spec dictionary
        apispec (APISpec): APISpec object to generate arguments for
    
    Returns:
        dict: APISpec `path` funtion argument dictionary
    """

    params = {
        "path": rule_to_path(rule),
        "operations": dict_to_apispec_operations(
            spec_dict.get("_operations", {}), apispec
        ),
    }

    # Add URL arguments to operations
    if rule.arguments:
        for op in spec_dict.get("_operations", {}).keys():
            params["operations"][op].update({"parameters": rule_to_params(rule)})

    # Merge in non-special spec elements
    for k, v in spec_dict.items():
        if not k.startswith("_"):
            params[k] = v

    return params


def dict_to_apispec_operations(operations_spec_dict: dict, apispec: APISpec):
    """Generate APISpec `operations` argument from a flask View

    Args:
        operations_spec_dict (dict): Operations API spec dictionary
        apispec (APISpec): APISpec object to generate arguments for

    Returns:
        dict: APISpec `operations` dictionary
    """

    # Build dictionary of operations (HTTP methods)
    ops = {}
    for operation, meth_spec in operations_spec_dict.items():

        ops[operation] = {}

        # Add input schema
        if "_params" in meth_spec:
            request_schema = convert_to_schema_or_json(
                meth_spec.get("_params"), apispec
            )
            if request_schema:
                ops[operation]["requestBody"] = {
                    "content": {"application/json": {"schema": request_schema}}
                }

        # Add output schema
        if "_schema" in meth_spec:
            ops[operation]["responses"] = {}
            for code, schema in meth_spec.get("_schema", {}).items():
                ops[operation]["responses"][code] = {
                    "description": HTTPStatus(code).phrase,
                    "content": {
                        "application/json": {
                            "schema": convert_to_schema_or_json(schema, apispec)
                        }
                    },
                }
        else:
            # If no explicit responses are known, populate with defaults
            ops[operation]["responses"] = {
                200: {
                    "description": meth_spec.get("description")
                    or HTTPStatus(200).phrase
                }
            }

        # Merge in non-special spec elements
        for k, v in meth_spec.items():
            if not k.startswith("_"):
                ops[operation][k] = v

    return ops
