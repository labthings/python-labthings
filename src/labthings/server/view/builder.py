from labthings.core.tasks import taskify
from labthings.server.types import (
    value_to_field,
    data_dict_to_schema,
    function_signature_to_schema,
)
from labthings.server.decorators import (
    ThingProperty,
    PropertySchema,
    ThingAction,
    marshal_task,
    use_args,
    Doc,
    Safe,
    Idempotent,
)
from . import View

from flask import send_from_directory
import uuid


def property_of(
    property_object, property_name, name: str = None, readonly=False, description=None
):

    # Create a class name
    if not name:
        name = type(property_object).__name__ + f"_{property_name}"

    # Create inner functions
    def _get(self):
        return getattr(property_object, property_name)

    def _post(self, args):
        setattr(property_object, property_name, args)
        return getattr(property_object, property_name)

    def _put(self, args):
        getattr(property_object, property_name).update(args)
        return getattr(property_object, property_name)

    # Generate a basic property class
    generated_class = type(
        name,
        (View, object),
        {
            "property_object": property_object,
            "property_name": property_name,
            "get": _get,
        },
    )

    # Override read-write capabilities
    if not readonly:
        generated_class.post = _post
        generated_class.methods.add("POST")
        # Enable PUT requests for dictionaries
        if type(getattr(property_object, property_name)) is dict:
            generated_class.put = _put
            generated_class.methods.add("PUT")

    # Add decorators for arguments etc
    initial_property_value = getattr(property_object, property_name)
    if type(initial_property_value) is dict:
        property_schema = data_dict_to_schema(initial_property_value)
    else:
        property_schema = value_to_field(initial_property_value)

    generated_class = PropertySchema(property_schema)(generated_class)
    generated_class = ThingProperty(generated_class)

    if description:
        generated_class = Doc(description=description, summary=description)(
            generated_class
        )

    return generated_class


def action_from(
    function,
    name: str = None,
    description=None,
    task=False,
    safe=False,
    idempotent=False,
):

    # Create a class name
    if not name:
        name = f"Action_{function.__name__}"

    # Create schema
    action_schema = function_signature_to_schema(function)

    # Handle taskification
    if task:
        function = taskify(function)

    # Create inner functions
    def _post(self, args):
        return function(**args)

    # Generate a basic property class
    generated_class = type(name, (View, object), {"post": _post})

    # Add decorators for arguments etc

    generated_class.post = use_args(action_schema)(generated_class.post)

    if task:
        generated_class.post = marshal_task(generated_class.post)

    generated_class = ThingAction(generated_class)

    if description:
        generated_class = Doc(description=description, summary=description)(
            generated_class
        )

    if safe:
        generated_class = Safe(generated_class)

    if idempotent:
        generated_class = Idempotent(generated_class)

    return generated_class


def static_from(static_folder: str, name=None):

    # Create a class name
    if not name:
        uid = uuid.uuid4()
        name = f"static-{uid}"

    # Create inner functions
    def _get(self, path):
        return send_from_directory(static_folder, path)

    # Generate a basic property class
    generated_class = type(name, (View, object), {"get": _get})

    return generated_class
