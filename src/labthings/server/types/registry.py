from labthings.server import fields

from marshmallow.base import FieldABC
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Dict, Tuple, List
from uuid import UUID
from inspect import _empty


PRIMITIVE_TYPES = [
    bool,
    date,
    datetime,
    Decimal,
    float,
    int,
    str,
    time,
    timedelta,
    UUID,
    dict,
    Dict,
    List,
    list,
    bytes,
]


def _field_factory(field: FieldABC):
    """
    Maps a marshmallow field into a field factory
    """

    def _(subtypes: Tuple[type], **opts) -> FieldABC:
        return field(**opts)

    _.__name__ = f"{field.__name__}FieldFactory"
    return _


class TypeRegistry:
    """
    Default implementation of :class:`~marshmallow_annotations.base.TypeRegistry`.
    """

    def __init__(self) -> None:
        self._registry = {
            k: _field_factory(v)
            for k, v in {
                bool: fields.Boolean,
                date: fields.Date,
                datetime: fields.DateTime,
                Decimal: fields.Decimal,
                float: fields.Float,
                int: fields.Integer,
                str: fields.String,
                time: fields.Time,
                timedelta: fields.TimeDelta,
                UUID: fields.UUID,
                dict: fields.Dict,
                Dict: fields.Dict,
                bytes: fields.Bytes,
                _empty: fields.Field,
            }.items()
        }

    def register(self, target: type, constructor) -> None:
        self._registry[target] = constructor

    def get(self, target: type):
        converter = self._registry.get(target)

        if converter is None:
            raise TypeError(f"No field factory found for {target!r}")
        return converter

    def has(self, target: type) -> bool:
        return target in self._registry
