from flask import make_response, current_app

# Flask JSON encoder so we get UUID, datetime etc support
from flask.json import JSONEncoder
import json
import cbor2


from ..core.utilities import PY3


class LabThingsJSONEncoder(JSONEncoder):
    """
    A custom JSON encoder, with type conversions for PiCamera fractions, Numpy integers, and Numpy arrays
    """

    def default(self, o):
        if isinstance(o, set):
            return list(o)
        return JSONEncoder.default(self, o)


def encode_json(data, encoder=LabThingsJSONEncoder, **settings):
    """Makes JSON encoded data using the LabThings JSON encoder"""
    return json.dumps(data, cls=encoder, **settings) + "\n"


def output_json(data, code, headers=None):
    """Makes a Flask response with a JSON encoded body, using app JSON settings"""

    settings = current_app.config.get("LABTHINGS_JSON", {})
    encoder = current_app.json_encoder

    if current_app.debug:
        settings.setdefault("indent", 4)
        settings.setdefault("sort_keys", not PY3)

    dumped = encode_json(data, encoder=encoder, **settings)

    resp = make_response(dumped, code)
    resp.headers.extend(headers or {})
    return resp


def encode_cbor(data, **settings):
    """Makes CBOR encoded data using the default CBOR encoder"""
    return cbor2.dumps(data, **settings)


def output_cbor(data, code, headers=None):
    """Makes a Flask response with a CBOR encoded body, using app CBOR settings"""

    settings = current_app.config.get("LABTHINGS_CBOR", {})

    dumped = encode_cbor(data, **settings)

    resp = make_response(dumped, code)
    resp.headers.extend(headers or {})
    resp.mimetype = "application/cbor"
    return resp


DEFAULT_REPRESENTATIONS = [
    ("application/json", output_json),
    ("application/cbor", output_cbor),
]
