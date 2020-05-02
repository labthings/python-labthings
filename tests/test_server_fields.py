from labthings.server import schema
from labthings.server import fields

from marshmallow import ValidationError
import pickle

import pytest


def test_bytes_in_schema():
    test_schema = schema.Schema.from_dict({"b": fields.Bytes()})()

    obj = type("obj", (object,), {"b": pickle.dumps(object())})

    assert test_schema.dump(obj) == {
        "b": b"\x80\x04\x95\x1a\x00\x00\x00\x00\x00\x00\x00\x8c\x08builtins\x94\x8c\x06object\x94\x93\x94)\x81\x94.",
    }


def test_bytes_validate():
    assert fields.Bytes()._validate(pickle.dumps(object())) is None


def test_bytes_validate_wrong_type():
    with pytest.raises(ValidationError):
        fields.Bytes()._validate(object())


def test_bytes_validate_bad_data():
    with pytest.raises(ValidationError):
        fields.Bytes()._validate(b"")
