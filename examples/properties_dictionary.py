from fractions import Fraction

from labthings.server.quick import create_app
from labthings.server.decorators import ThingProperty, PropertySchema
from labthings.server.view import View
from labthings.server.find import find_component
from labthings.server.types import data_dict_to_schema

import logging
from pprint import pprint

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

"""
Class for our lab component functionality. This could include serial communication,
equipment API calls, network requests, or a "virtual" device as seen here.
"""


class MyComponent:
    def __init__(self):
        self.x_range = range(0, 10)

        self.magic_denoise = 200
        self.some_property = Fraction(5, 2)
        self.some_string = "Hello"

        self.prop_keys = ["magic_denoise", "some_property", "some_string", "x_range"]

    def get_state(self):
        return {key: getattr(self, key) for key in self.prop_keys}

    def set_state(self, new_state):
        for key in self.prop_keys:
            if key in new_state:
                setattr(self, key, new_state.get(key))
        return self.get_state()

    def get_state_schema(self):
        s = data_dict_to_schema(self.get_state())
        return s


my_component = MyComponent()


"""
Create a view to view and change our magic_denoise value, and register is as a Thing property
"""


@ThingProperty  # Register this view as a Thing Property
@PropertySchema(my_component.get_state_schema())
class MapProperty(View):

    # Main function to handle GET requests (read)
    def get(self):
        """Show the current magic_denoise value"""

        # When a GET request is made, we'll find our attached component
        found_my_component = find_component("org.labthings.example.mycomponent")
        return found_my_component.get_state()

    # Main function to handle PUT requests (update)
    def put(self, new_property_value):
        """Change the current magic_denoise value"""

        # Find our attached component
        found_my_component = find_component("org.labthings.example.mycomponent")

        # Apply the new value
        return found_my_component.set_state(new_property_value)


# Create LabThings Flask app
app, labthing = create_app(
    __name__,
    prefix="/api",
    title=f"My Lab Device API",
    description="Test LabThing-based API",
    version="0.1.0",
)

# Attach an instance of our component
labthing.add_component(my_component, "org.labthings.example.mycomponent")

# Add routes for the API views we created
labthing.add_view(MapProperty, "/props")

# Start the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000", threaded=True, debug=True, use_reloader=False)
