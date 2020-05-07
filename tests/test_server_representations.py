from labthings.server import representations
from flask import Response
import cbor2
import pytest
import pickle
import json


@pytest.fixture
def labthings_json_encoder():
    return representations.LabThingsJSONEncoder


def test_encoder_default_exception(labthings_json_encoder):
    with pytest.raises(TypeError):
        labthings_json_encoder().default("")


def test_encode_json(labthings_json_encoder):
    data = {
        "key": "value",
        "blob": pickle.dumps(object()),
    }

    out = representations.encode_json(data, encoder=labthings_json_encoder)
    out_dict = json.loads(out)
    assert "blob" in out_dict
    assert isinstance(out_dict.get("blob"), str)


def test_output_json(app_ctx):
    data = {
        "key": "value",
    }

    with app_ctx.test_request_context():
        response = representations.output_json(data, 200)
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"
        assert response.data == b'{"key": "value"}\n'


def test_pretty_output_json(app_ctx_debug):
    data = {
        "key": "value",
    }

    with app_ctx_debug.test_request_context():
        response = representations.output_json(data, 200)
        assert response.data == b'{\n    "key": "value"\n}\n'


def test_encode_cbor():
    data = {
        "key": "value",
        "blob": pickle.dumps(object()),
    }
    assert cbor2.loads(representations.encode_cbor(data)) == data


def test_output_cbor(app_ctx):
    data = {
        "key": "value",
        "blob": pickle.dumps(object()),
    }

    with app_ctx.test_request_context():
        response = representations.output_cbor(data, 200)
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/cbor"
        assert cbor2.loads(response.data) == data
