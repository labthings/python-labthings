from labthings import schema
from labthings import fields

from marshmallow import ValidationError
from base64 import b64encode
import pickle

import pytest


def test_bytes_encode():
    test_schema = schema.Schema.from_dict({"b": fields.Bytes()})()

    obj = type("obj", (object,), {"b": pickle.dumps(object())})

    assert test_schema.dump(obj) == {
        "b": obj.b,
    }


def test_bytes_decode():
    test_schema = schema.Schema.from_dict({"b": fields.Bytes()})()

    data = {"b": pickle.dumps(object())}

    assert test_schema.load(data) == data


def test_bytes_decode_string():
    test_schema = schema.Schema.from_dict({"b": fields.Bytes()})()

    data = {"b": pickle.dumps(object())}
    encoded_data = {"b": b64encode(data["b"]).decode()}

    assert test_schema.load(encoded_data) == data


def test_bytes_validate():
    assert fields.Bytes()._validate(pickle.dumps(object())) is None


def test_bytes_validate_wrong_type():
    with pytest.raises(ValidationError):
        fields.Bytes()._validate(object())


def test_bytes_validate_bad_data():
    with pytest.raises(ValidationError):
        fields.Bytes()._validate(b"")
