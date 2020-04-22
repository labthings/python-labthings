from flask import make_response, current_app
from json import dumps, JSONEncoder

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

    # always end the json dumps with a new line
    # see https://github.com/mitsuhiko/flask/pull/1262
    dumped = dumps(data, cls=encoder, **settings) + "\n"

    return dumped


def output_json(data, code, headers=None):
    """Makes a Flask response with a JSON encoded body, using app JSON settings"""

    settings = current_app.config.get("LABTHINGS_JSON", {})
    encoder = current_app.json_encoder

    # If we're in debug mode, and the indent is not set, we set it to a
    # reasonable value here.  Note that this won't override any existing value
    # that was set.  We also set the "sort_keys" value.
    if current_app.debug:
        settings.setdefault("indent", 4)
        settings.setdefault("sort_keys", not PY3)

    dumped = encode_json(data, encoder=encoder, **settings)

    resp = make_response(dumped, code)
    resp.headers.extend(headers or {})
    return resp


DEFAULT_REPRESENTATIONS = [("application/json", output_json)]
