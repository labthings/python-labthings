# Flask JSON encoder so we get UUID, datetime etc support
import json
from base64 import b64encode
from collections import UserString

from flask.json import JSONEncoder


class LabThingsJSONEncoder(JSONEncoder):
    """A custom JSON encoder, with type conversions for PiCamera fractions, Numpy integers, and Numpy arrays"""

    def default(self, o):
        """

        :param o:

        """
        if isinstance(o, set):
            return list(o)
        if isinstance(o, bytes):
            try:  # Try unicode
                return o.decode()
            except UnicodeDecodeError:  # Otherwise, base64
                return b64encode(o).decode()
        if isinstance(o, UserString):
            return str(o)
        return JSONEncoder.default(self, o)


def encode_json(data, encoder=LabThingsJSONEncoder, **settings):
    """Makes JSON encoded data using the LabThings JSON encoder

    :param data:
    :param encoder:  (Default value = LabThingsJSONEncoder)
    :param **settings:

    """
    return json.dumps(data, cls=encoder, **settings) + "\n"
