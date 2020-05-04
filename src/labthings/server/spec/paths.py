# -*- coding: utf-8 -*-

import re

import werkzeug.routing

PATH_RE = re.compile(r"<(?:[^:<>]+:)?([^<>]+)>")


def rule_to_path(rule):
    """Convert a Flask rule into an APISpec formatted URL path
    
    Args:
        rule: Flask rule object
    
    Returns:
        str: URL path
    """
    return PATH_RE.sub(r"{\1}", rule.rule)


# Conversion map of werkzeug rule converters to Javascript schema types
CONVERTER_MAPPING = {
    werkzeug.routing.UnicodeConverter: ("string", None),
    werkzeug.routing.IntegerConverter: ("integer", "int32"),
    werkzeug.routing.FloatConverter: ("number", "float"),
}

DEFAULT_TYPE = ("string", None)


def rule_to_params(rule, overrides=None):
    """Convert a Flask rule into APISpec URL parameters description
    
    Args:
        rule: Flask rule object
        overrides (dict, optional): Optional dictionary to override params with
    
    Returns:
        dict: Dictionary of URL parameters
    """
    overrides = overrides or {}
    result = [
        argument_to_param(argument, rule, overrides.get(argument, {}))
        for argument in rule.arguments
    ]
    for key in overrides.keys():
        if overrides[key].get("in") in ("header", "query"):
            overrides[key]["name"] = overrides[key].get("name", key)
            result.append(overrides[key])
    return result


def argument_to_param(argument, rule, override=None):
    """Convert a Flask rule into APISpec URL parameters description
    
    Args:
        argument (str): URL argument
        rule: Flask rule object
        override (dict, optional): Optional dictionary to override params with
    
    Returns:
        dict: Dictionary of URL parameter description
    """
    param = {"in": "path", "name": argument, "required": True}
    type_, format_ = CONVERTER_MAPPING.get(
        # skipcq: PYL-W0212
        type(rule._converters[argument]),
        DEFAULT_TYPE,
    )
    param["schema"] = {}
    param["schema"]["type"] = type_
    if format_ is not None:
        param["format"] = format_
    if rule.defaults and argument in rule.defaults:
        param["default"] = rule.defaults[argument]
    param.update(override or {})
    return param
