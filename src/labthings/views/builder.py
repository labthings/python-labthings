import glob
import os
import uuid
from typing import Type

from flask import abort, send_file

from . import View, described_operation


def static_from(static_folder: str, name=None) -> Type[View]:
    """
    :param static_folder: str:
    :param name:  (Default value = None)
    """

    # Create a class name
    if not name:
        uid = uuid.uuid4()
        name = f"static-{uid}"

    # Create inner functions
    @described_operation
    def _get(_, path=""):
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

    _get.summary = "Serve static files"
    _get.description = (
        "Files and folders within this path will be served from a static directory."
    )
    _get.responses = {
        "200": {
            "description": "Static file",
        },
        "404": {
            "description": "Static file not found",
        },
    }

    # Generate a basic property class
    generated_class = type(
        name,
        (View, object),
        {
            "get": _get,
            "parameters": [
                {
                    "name": "path",
                    "in": "path",
                    "description": "Path to the static file",
                    "required": True,
                    "schema": {"type": "string"},
                    "example": "style.css",
                }
            ],
        },
    )

    return generated_class
