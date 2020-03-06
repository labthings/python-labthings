import uuid
import types
import functools

from labthings.server.quick import create_app
from labthings.server.view import View
from labthings.server.decorators import (
    ThingProperty,
    PropertySchema,
    use_args,
)

from labthings.server.types import value_to_field, data_dict_to_schema

from components.pdf_component import PdfComponent


def copy_func(f):
    """Based on http://stackoverflow.com/a/6528148/190597 (Glenn Maynard)"""
    g = types.FunctionType(
        f.__code__,
        f.__globals__,
        name=f.__name__,
        argdefs=f.__defaults__,
        closure=f.__closure__,
    )
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    return g


class BasePropertyResource(View):
    def __init__(self):
        super().__init__()
        """
        Properties to be added by constructor function:
        property_object: Object containing the property
        property_name: String name of property of object
        """

    def _get(self):
        return getattr(self.property_object, self.property_name)

    def _post(self, args):
        setattr(self.property_object, self.property_name, args)
        return getattr(self.property_object, self.property_name)

    def _put(self, args):
        if type(getattr(self.property_object, self.property_name)) != dict:
            raise TypeError("Cannot PUT to a property that isn't an object/dictionary")
        getattr(self.property_object, self.property_name).update(args)
        return getattr(self.property_object, self.property_name)


def gen_property(property_object, property_name, name: str = None, post=True):

    # Create a class name
    if not name:
        name = type(property_object).__name__ + f"_{property_name}"

    # Generate a basic property class
    generated_class = type(
        name,
        (BasePropertyResource, object),
        {
            "property_object": property_object,
            "property_name": property_name,
            "get": copy_func(BasePropertyResource._get),
        },
    )

    # Enable PUT requests for dictionaries
    if type(getattr(property_object, property_name)) == dict:
        generated_class.put = copy_func(BasePropertyResource._put)

    # Override read-write capabilities
    if post:
        generated_class.post = copy_func(BasePropertyResource._post)

    # Add decorators for arguments etc
    initial_property_value = getattr(property_object, property_name)
    if type(initial_property_value) == dict:
        property_schema = data_dict_to_schema(initial_property_value)
    else:
        property_schema = value_to_field(initial_property_value)

    generated_class = PropertySchema(property_schema)(generated_class)
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
labthing.add_view(gen_property(my_component, "magic_dictionary"), "/dictionary")

# Start the app
# if __name__ == "__main__":
#    app.run(host="0.0.0.0", port="5000", threaded=True, debug=True, use_reloader=False)
