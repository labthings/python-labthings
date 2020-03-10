from flask import make_response, current_app
from json import dumps

from ..core.utilities import PY3


def encode_json(data):
    """Makes JSON encoded data using the current Flask apps JSON settings"""

    settings = current_app.config.get("LABTHINGS_JSON", {})
    encoder = current_app.json_encoder

    # If we're in debug mode, and the indent is not set, we set it to a
    # reasonable value here.  Note that this won't override any existing value
    # that was set.  We also set the "sort_keys" value.
    if current_app.debug:
        settings.setdefault("indent", 4)
        settings.setdefault("sort_keys", not PY3)

    # always end the json dumps with a new line
    # see https://github.com/mitsuhiko/flask/pull/1262
    dumped = dumps(data, cls=encoder, **settings) + "\n"

    return dumped


def output_json(data, code, headers=None):
    """Makes a Flask response with a JSON encoded body"""

    dumped = encode_json(data) + "\n"

    resp = make_response(dumped, code)
    resp.headers.extend(headers or {})
    return resp


DEFAULT_REPRESENTATIONS = [("application/json", output_json)]
