from .registry import TypeRegistry
from labthings.server import fields

from typing import List, Tuple
from inspect import Parameter
from marshmallow.base import FieldABC

import inspect

NoneType = type(None)


class AnnotationConverter:
    def __init__(self):
        self._registry = TypeRegistry()
        self._registry.register(List, self._list_converter)
        self._registry.register(list, self._list_converter)

    def _list_converter(self, subtypes: Tuple[type], **opts) -> FieldABC:
        sub_opts = opts.pop("_interior", {})
        return fields.List(self.convert(subtypes[0], **sub_opts), **opts)

    def convert(self, parameter, **kwargs) -> FieldABC:
        # sane defaults
        allow_none = False
        required = True
        optional = False
        subtypes = ()

        if isinstance(parameter, Parameter):
            typehint = parameter.annotation
            optional = not (parameter.default is parameter.empty)
            # Skip unbound arguments (e.g. *args, **kwargs) until we find a better way to handle them
            if (
                parameter.kind == Parameter.VAR_POSITIONAL
                or parameter.kind == Parameter.VAR_KEYWORD
            ):
                return None
        elif isinstance(parameter, type):
            typehint = parameter
        else:
            typehint = type(parameter)

        if optional:
            allow_none = True
            required = False

        if isinstance(parameter, Parameter):
            # Get subtypes
            subtypes = getattr(typehint, "__args__", ())
            if subtypes != ():
                typehint = typehint.__origin__

            # Get default
            if not (parameter.default is parameter.empty):
                kwargs.setdefault("default", parameter.default)
                kwargs.setdefault("example", parameter.default)

        kwargs.setdefault("allow_none", allow_none)
        kwargs.setdefault("required", required)

        field_constructor = self._registry.get(typehint)
        return field_constructor(subtypes, **kwargs)


def function_signature_to_schema(function: callable):
    """
    """
    converter = AnnotationConverter()

    schema_dict = {}
    params = inspect.signature(function).parameters

    for k, p in params.items():
        param_schema = converter.convert(p)
        if param_schema:
            schema_dict[k] = converter.convert(p)

    return schema_dict
