from . import View, Action, Property
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
    name = name or type(property_object).__name__ + f"_{property_name}"

    # Create inner functions
    def _read(self):
        return getattr(property_object, property_name)

    def _write(self, args):
        setattr(property_object, property_name, args)
        return getattr(property_object, property_name)

    def _update(self, args):
        getattr(property_object, property_name).update(args)
        return getattr(property_object, property_name)

    # Override read-write capabilities
    if readonly:
        writeproperty_forwarder = None
    else:
        # Enable update PUT requests for dictionaries
        if type(getattr(property_object, property_name)) is dict:
            writeproperty_forwarder = _update
        else:
            writeproperty_forwarder = _write

    # Generate property
    return Property(
        name,
        writeproperty_forwarder,
        _read,
        readonly=readonly,
        description=description,
        schema=schema,
        semtype=semtype,
    )


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
    wait_for: int = 1,
    default_stop_timeout: int = None,
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
    name = name or type(action_object).__name__ + f"_{action_name}"

    # Get pointer to action function
    action_f = getattr(action_object, action_name)
    # Ensure action function is actually a function
    if not callable(action_f):
        raise TypeError(
            f"Attribute {action_name} of {action_object} must be a callable"
        )

    # Create inner functions
    def _post(self):
        return action_f()

    def _post_with_args(self, args):
        return action_f(**args)

    # Add decorators for arguments etc
    if args is not None:
        invokeaction_forwarder = _post_with_args
    else:
        invokeaction_forwarder = _post

    return Action(
        name,
        invokeaction_forwarder,
        description=description,
        safe=safe,
        idempotent=idempotent,
        args=args,
        schema=schema,
        semtype=semtype,
        wait_for=wait_for,
        default_stop_timeout=default_stop_timeout,
    )


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
