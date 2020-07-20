from . import View, ActionView, PropertyView
from .. import fields
from ..semantics.base import Semantic

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
    schema=None,
    semtype=None,
):
    """
    :param property_object: object: Python object containing the property
    :param property_name: str: Name of the property on the Python object
    :param name: str:  (Default value = None)
    :param readonly:  (Default value = False) Is the property read-only?
    :param description:  (Default value = None) Human readable description of the property
    :param schema:  (Default value = None) Marshmallow schema for the property
    :type schema: :class:`labthings.fields.Field` or :class:`labthings.schema.Schema`
    :param semtype:  (Default value = None) Optional semantic object containing schema and annotations
    :type semtype: :class:`labthings.semantics.Semantic`
    """

    # Create a class name
    if not name:
        name = type(property_object).__name__ + f"_{property_name}"

    # Create inner functions
    def _read(self):
        """ """
        return getattr(property_object, property_name)

    def _write(self, args):
        """

        :param args: 

        """
        setattr(property_object, property_name, args)
        return getattr(property_object, property_name)

    def _update(self, args):
        """

        :param args: 

        """
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
        # Normally, use PUT to write property
        else:
            generated_class.put = _write
            generated_class.methods.add("PUT")

    # Add decorators for arguments etc
    if schema:
        generated_class.schema = schema

    if description:
        generated_class.description = description
        generated_class.summary = description.partition("\n")[0].strip()

    # Apply semantic type last, to ensure this is always used
    if semtype:
        if isinstance(semtype, str):
            generated_class.semtype = semtype
        elif isinstance(semtype, Semantic):
            generated_class = semtype(generated_class)
        else:
            raise TypeError(
                "Unsupported type for semtype. Must be a string or Semantic object"
            )
    return generated_class


def action_from(
    action_object: object,
    action_name: str,
    name: str = None,
    safe=False,
    idempotent=False,
    description=None,
    args=None,
    schema=None,
    semtype=None,
):
    """
    :param action_object: object: Python object containing the action method
    :param action_name: str: Name of the method on the Python object
    :param name: str:  (Default value = None)
    :param safe:  (Default value = False) Is the action safe
    :param idempotent:  (Default value = False) Is the action idempotent
    :param description:  (Default value = None) Human readable description of the property
    :param args:  (Default value = fields.Field()) Marshmallow schema for the method arguments
    :type args: :class:`labthings.schema.Schema`
    :param schema:  (Default value = fields.Field()) Marshmallow schema for the method response
    :type schema: :class:`labthings.fields.Field` or :class:`labthings.schema.Schema`
    :param semtype:  (Default value = None) Optional semantic object containing schema and annotations
    :type semtype: :class:`labthings.semantics.Semantic`
    """

    # Create a class name
    if not name:
        name = type(action_object).__name__ + f"_{action_name}"

    # Get pointer to action function
    action_f = getattr(action_object, action_name)
    # Ensure action function is actually a function
    if not callable(action_f):
        raise TypeError(
            f"Attribute {action_name} of {action_object} must be a callable"
        )

    # Create inner functions
    def _post(self):
        """ """
        return action_f()

    def _post_with_args(self, args):
        """

        :param args: 

        """
        return action_f(**args)

    # Add decorators for arguments etc
    if args is not None:
        generated_class = type(name, (ActionView, object), {"post": _post_with_args})
        generated_class.args = args
    else:
        generated_class = type(name, (ActionView, object), {"post": _post})

    if schema:
        generated_class.schema = schema

    if description:
        generated_class.description = description
        generated_class.summary = description.partition("\n")[0].strip()

    # Apply semantic type last, to ensure this is always used
    if semtype:
        if isinstance(semtype, str):
            generated_class.semtype = semtype
        elif isinstance(semtype, Semantic):
            generated_class = semtype(generated_class)
        else:
            raise TypeError(
                "Unsupported type for semtype. Must be a string or Semantic object"
            )

    generated_class.safe = safe
    generated_class.idempotent = idempotent

    return generated_class


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
    generated_class = type(name, (View, object), {"get": _get})

    return generated_class
