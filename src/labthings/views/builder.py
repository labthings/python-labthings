import glob
import os
import uuid

from flask import abort, send_file
from flask.views import MethodView


def static_from(static_folder: str, name=None):
    """
    :param static_folder: str: 
    :param name:  (Default value = None)
    """

    # Create a class name
    if not name:
        uid = uuid.uuid4()
        name = f"static-{uid}"

    # Create inner functions
    def _get(self, path=""):
        """
        :param path:  (Default value = "")
        """
        full_path = os.path.join(static_folder, path)
        if not os.path.exists(full_path):
            return abort(404)

        if os.path.isfile(full_path):
            return send_file(full_path)

        if os.path.isdir(full_path):
            indexes = glob.glob(os.path.join(full_path, "index.*"))
            if not indexes:
                return abort(404)
            return send_file(indexes[0])

    # Generate a basic property class
    generated_class = type(name, (MethodView, object), {"get": _get})

    return generated_class
