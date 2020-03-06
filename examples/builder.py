import uuid

from labthings.server.quick import create_app
from labthings.server.view import View
from labthings.server.decorators import (
    ThingProperty,
    PropertySchema,
    use_args,
)

from labthings.server.types import value_to_field

from components.pdf_component import PdfComponent


class BasePropertyResource(View):
    def __init__(self):
        super().__init__()
        """
        Properties to be added by constructor function:
        property_object: Object containing the property
        property_name: String name of property of object
        """

    def get(self):
        return getattr(self.property_object, self.property_name)

    def post(self, args):
        setattr(self.property_object, self.property_name, args)
        return getattr(self.property_object, self.property_name)


def gen_property(property_object, property_name, name: str = None, post=True):

    # Create a class name
    if not name:
        name = type(property_object).__name__ + f"_{property_name}"

    # Generate a basic property class
    generated_class = type(
        name,
        (BasePropertyResource, object),
        {"property_object": property_object, "property_name": property_name,},
    )

    # Override read-write capabilities
    if not post:
        generated_class.post = None

    # Add decorators for arguments etc
    initial_property_value = getattr(property_object, property_name)
    generated_class = PropertySchema(value_to_field(initial_property_value))(
        generated_class
    )
    generated_class = ThingProperty(generated_class)

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
labthing.add_view(gen_property(my_component, "magic_denoise"), "/denoise")

# Start the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000", threaded=True, debug=True, use_reloader=False)
