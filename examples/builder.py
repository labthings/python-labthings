import uuid
import types
import functools

from labthings.server.quick import create_app
from labthings.server.view import View
from labthings.server.decorators import ThingProperty, PropertySchema, use_args, Doc

from labthings.server.types import value_to_field, data_dict_to_schema

from components.pdf_component import PdfComponent


def gen_property(
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
        # Enable PUT requests for dictionaries
        if type(getattr(property_object, property_name)) == dict:
            generated_class.put = _put

    # Add decorators for arguments etc
    initial_property_value = getattr(property_object, property_name)
    if type(initial_property_value) == dict:
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


# Create LabThings Flask app
app, labthing = create_app(
    __name__,
    prefix="/api",
    title=f"My Lab Device API",
    description="Test LabThing-based API",
    version="0.1.0",
)

# Attach an instance of our component
my_component = PdfComponent()
labthing.add_component(my_component, "org.labthings.example.mycomponent")

# Add routes for the API views we created
labthing.add_view(
    gen_property(my_component, "magic_denoise", description="A magic denoise property"),
    "/denoise",
)
labthing.add_view(
    gen_property(
        my_component,
        "magic_dictionary",
        description="A big dictionary of little properties",
    ),
    "/dictionary",
)

# Start the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000", threaded=True, debug=True, use_reloader=False)
