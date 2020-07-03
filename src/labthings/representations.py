from flask import make_response, current_app

# Flask JSON encoder so we get UUID, datetime etc support
from flask.json import JSONEncoder
from base64 import b64encode
import json


from .utilities import PY3


class LabThingsJSONEncoder(JSONEncoder):
    """
    A custom JSON encoder, with type conversions for PiCamera fractions, Numpy integers, and Numpy arrays
    """

    def default(self, o):
        if isinstance(o, set):
            return list(o)
        if isinstance(o, bytes):
            try:  # Try unicode
                return o.decode()
            except UnicodeDecodeError:  # Otherwise, base64
                return b64encode(o).decode()
        return JSONEncoder.default(self, o)


def encode_json(data, encoder=LabThingsJSONEncoder, **settings):
    """Makes JSON encoded data using the LabThings JSON encoder"""
    return json.dumps(data, cls=encoder, **settings) + "\n"


def output_json(data, code, headers=None):
    """Makes a Flask response with a JSON encoded body, using app JSON settings"""

    settings = current_app.config.get("LABTHINGS_JSON", {})
    encoder = (
        current_app.config.get("LABTHINGS_JSON_ENCODER", {}) or LabThingsJSONEncoder
    )

    if current_app.debug:
        settings.setdefault("indent", 4)
        settings.setdefault("sort_keys", not PY3)

    dumped = encode_json(data, encoder=encoder, **settings)

    resp = make_response(dumped, code)
    resp.headers.extend(headers or {})
    resp.mimetype = "application/json"
    return resp


DEFAULT_REPRESENTATIONS = [
    ("application/json", output_json),
]
