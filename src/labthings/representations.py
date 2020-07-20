from flask import make_response, current_app
from collections import OrderedDict

from .json.encoder import LabThingsJSONEncoder, encode_json
from .json.encoder import JSONEncoder as FlaskJSONEncoder
from .find import current_labthing
from .utilities import PY3


def output_json(data, code, headers=None):
    """Makes a Flask response with a JSON encoded body, using app JSON settings

    :param data: Data to be serialised
    :param code: HTTP response code
    :param headers: HTTP response headers (Default value = None)

    """

    settings = current_app.config.get("LABTHINGS_JSON", {})

    if current_labthing():
        encoder = current_labthing().json_encoder
    else:
        encoder = getattr(current_app, "json_encoder", None) or FlaskJSONEncoder

    if current_app.debug:
        settings.setdefault("indent", 4)
        settings.setdefault("sort_keys", not PY3)

    dumped = encode_json(data, encoder=encoder, **settings)

    resp = make_response(dumped, code)
    resp.headers.extend(headers or {})
    resp.mimetype = "application/json"
    return resp


DEFAULT_REPRESENTATIONS = OrderedDict({"application/json": output_json,})
