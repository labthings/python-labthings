from labthings.server.types import (
    value_to_field,
    data_dict_to_schema,
    function_signature_to_schema,
)
from labthings.server.decorators import (
    PropertySchema,
    use_args,
    Doc,
    Safe,
    Idempotent,
    Semtype,
)
from . import View, ActionView, PropertyView
from ..spec.utilities import compile_view_spec

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
    initial_property_value = getattr(property_object, property_name)
    if type(initial_property_value) is dict:
        property_schema = data_dict_to_schema(initial_property_value)
    else:
        property_schema = value_to_field(initial_property_value)

    generated_class = PropertySchema(property_schema)(generated_class)

    if description:
        generated_class = Doc(description=description, summary=description)(
            generated_class
        )

    if semtype:
        generated_class = Semtype(semtype)(generated_class)

    # Compile the generated views spec
    # Useful if its being attached to something other than a LabThing instance
    compile_view_spec(generated_class)

    return generated_class


def action_from(
    function,
    name: str = None,
    description=None,
    safe=False,
    idempotent=False,
    semtype=None,
):

    # Create a class name
    if not name:
        name = f"{function.__name__}_action"

    # Create schema
    action_schema = function_signature_to_schema(function)

    # Create inner functions
    def _post(self, args):
        return function(**args)

    # Generate a basic property class
    generated_class = type(name, (ActionView, object), {"post": _post})

    # Add decorators for arguments etc

    generated_class.post = use_args(action_schema)(generated_class.post)

    if description:
        generated_class = Doc(description=description, summary=description)(
            generated_class
        )

    if semtype:
        generated_class = Semtype(semtype)(generated_class)

    if safe:
        generated_class = Safe(generated_class)

    if idempotent:
        generated_class = Idempotent(generated_class)

    # Compile the generated views spec
    # Useful if its being attached to something other than a LabThing instance
    compile_view_spec(generated_class)

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
