from . import View, ActionView, PropertyView
from .. import fields

import os
import glob
from flask import send_file, abort
import uuid


def property_of(
    property_object: object,
    property_name: str,
    name: str = None,
    readonly=False,
    description=None,
    semtype=None,
    schema=fields.Field(),
    _legacy=False,  # Old structure where POST is used to write property
):

    # Create a class name
    if not name:
        name = type(property_object).__name__ + f"_{property_name}"

    # Create inner functions
    def _read(self):
        return getattr(property_object, property_name)

    def _write(self, args):
        setattr(property_object, property_name, args)
        return getattr(property_object, property_name)

    def _update(self, args):
        getattr(property_object, property_name).update(args)
        return getattr(property_object, property_name)

    # Generate a basic property class
    generated_class = type(
        name,
        (PropertyView, object),
        {
            "property_object": property_object,
            "property_name": property_name,
            "get": _read,
        },
    )

    # Override read-write capabilities
    if not readonly:
        # Enable update PUT requests for dictionaries
        if type(getattr(property_object, property_name)) is dict:
            generated_class.put = _update
            generated_class.methods.add("PUT")
        # If legacy mode, use POST to write property
        elif _legacy:
            generated_class.post = _write
            generated_class.methods.add("POST")
        # Normally, use PUT to write property
        else:
            generated_class.put = _write
            generated_class.methods.add("PUT")

    # Add decorators for arguments etc
    if schema:
        generated_class.schema = schema

    if description:
        generated_class.docs = {"description": description, "summary": description}

    if semtype:
        generated_class.semtype = semtype

    return generated_class


def action_from(
    function,
    name: str = None,
    description=None,
    safe=False,
    idempotent=False,
    args=None,
    schema=None,
    semtype=None,
):

    # Create a class name
    if not name:
        name = f"{function.__name__}_action"

    # Create inner functions
    def _post(self):
        return function()

    def _post_with_args(self, args):
        return function(**args)

    # Add decorators for arguments etc
    if args is not None:
        generated_class = type(name, (ActionView, object), {"post": _post_with_args})
        generated_class.args = args
    else:
        generated_class = type(name, (ActionView, object), {"post": _post})

    if schema:
        generated_class.schema = schema

    if description:
        generated_class.docs = {"description": description, "summary": description}

    if semtype:
        generated_class.semtype = semtype

    generated_class.safe = safe
    generated_class.idempotent = idempotent

    return generated_class


def static_from(static_folder: str, name=None):

    # Create a class name
    if not name:
        uid = uuid.uuid4()
        name = f"static-{uid}"

    # Create inner functions
    def _get(self, path=""):
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
    generated_class = type(name, (View, object), {"get": _get})

    return generated_class
