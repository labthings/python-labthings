from .registry import TypeRegistry
from .preprocess import make_primitive

from labthings.server import fields
from labthings.core.utilities import rapply

from marshmallow.base import FieldABC
from typing import List, Tuple, Union
import copy


class PropertyConverter:
    def __init__(self, required=True, allow_none=False):
        self._registry = TypeRegistry()
        self._registry.register(List, self._list_converter)
        self._registry.register(list, self._list_converter)

        self._required = required
        self._allow_none = allow_none

    @staticmethod
    def _list_converter(subtypes: Tuple[type], **opts) -> FieldABC:
        return fields.List(subtypes[0], **opts)

    def convert(self, value, **kwargs) -> FieldABC:
        allow_none = self._allow_none
        required = self._required
        example = value

        # set this after optional check
        if isinstance(value, (List, Tuple)) or type(value) is type(Union):
            subtypes = [self.convert(e) for e in value]
        else:
            subtypes = []

        typehint = type(value)

        kwargs.setdefault("allow_none", allow_none)
        kwargs.setdefault("required", required)
        kwargs.setdefault("example", example)

        field_constructor = self._registry.get(typehint)
        return field_constructor(subtypes, **kwargs)


def data_dict_to_schema(data_dict: dict):
    """Attempt to create a Marshmallow schema from a dictionary of data
    
    Args:
        data_dict (dict): Dictionary of data
    
    Returns:
        dict: Dictionary of Marshmallow fields matching input data types
    """
    converter = PropertyConverter(required=False)

    working_dict = copy.deepcopy(data_dict)

    working_dict = rapply(working_dict, make_primitive)
    working_dict = rapply(working_dict, converter.convert, apply_to_iterables=False)

    return working_dict


def value_to_field(value):
    converter = PropertyConverter()

    return converter.convert(value)
