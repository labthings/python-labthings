import random
import math
import logging

from labthings.server.quick import create_app
from labthings.server.decorators import (
    ThingProperty,
    PropertySchema,
    ThingAction,
    use_args,
    marshal_task,
    doc,
)
from labthings.server.view import View
from labthings.server.find import find_component
from labthings.server import fields
from labthings.core.utilities import path_relative_to
from labthings.core.tasks import taskify

from labthings.server.extensions import BaseExtension

import logging

logging.basicConfig(level=logging.DEBUG)

"""
Make our extension
"""


@ThingAction
class ExtensionMeasurementAction(View):
    # Expect JSON parameters in the request body.
    # Pass to post function as dictionary argument.
    @use_args(
        {
            "averages": fields.Integer(
                missing=10,
                example=10,
                description="Number of data sets to average over",
            )
        }
    )
    # Shorthand to say we're always going to return a Task object
    @marshal_task
    @doc(title="Averaged Measurement")
    # Main function to handle POST requests
    def post(self, args):
        """Start an averaged measurement"""

        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")

        # Get arguments and start a background task
        n_averages = args.get("averages")
        task = taskify(my_component.average_data)(n_averages)

        # Return the task information
        return task


def ext_on_register():
    logging.info("Extension registered")


def ext_on_my_component(component):
    logging.info(f"{component} registered and noticed by extension")


static_folder = path_relative_to(__file__, "static")

example_extension = BaseExtension(
    "org.labthings.examples.extension", static_folder=static_folder
)

example_extension.add_view(ExtensionMeasurementAction, "/measure", endpoint="measure")

example_extension.on_register(ext_on_register)
example_extension.on_component("org.labthings.example.mycomponent", ext_on_my_component)


"""
Class for our lab component functionality. This could include serial communication,
equipment API calls, network requests, or a "virtual" device as seen here.
"""


class MyComponent:
    def __init__(self):
        self.x_range = range(-100, 100)
        self.magic_denoise = 200

    def noisy_pdf(self, x, mu=0.0, sigma=25.0):
        """
        Generate a noisy gaussian function (to act as some pretend data)
        
        Our noise is inversely proportional to self.magic_denoise
        """
        x = float(x - mu) / sigma
        return (
            math.exp(-x * x / 2.0) / math.sqrt(2.0 * math.pi) / sigma
            + (1 / self.magic_denoise) * random.random()
        )

    @property
    def data(self):
        """
        Return a 1D data trace.
        """
        return [self.noisy_pdf(x) for x in self.x_range]


"""
Create a view to view and change our magic_denoise value, and register is as a Thing property
"""


@ThingProperty  # Register this view as a Thing Property
@PropertySchema(  # Define the data we're going to output (get), and what to expect in (post)
    fields.Integer(
        required=True,
        example=200,
        minimum=100,
        maximum=500,
        description="Value of magic_denoise",
    )
)
class DenoiseProperty(View):

    # Main function to handle GET requests (read)
    def get(self):
        """Show the current magic_denoise value"""

        # When a GET request is made, we'll find our attached component
        my_component = find_component("org.labthings.example.mycomponent")
        return my_component.magic_denoise

    # Main function to handle POST requests (write)
    def post(self, new_property_value):
        """Change the current magic_denoise value"""

        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")

        # Apply the new value
        my_component.magic_denoise = new_property_value

        return my_component.magic_denoise


"""
Create a view to quickly get some noisy data, and register is as a Thing property
"""


@ThingProperty
@PropertySchema(fields.List(fields.Float()))
class QuickDataProperty(View):
    # Main function to handle GET requests
    def get(self):
        """Show the current data value"""

        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")
        return my_component.data


# Create LabThings Flask app
app, labthing = create_app(
    __name__,
    prefix="/api",
    title="My Lab Device API",
    description="Test LabThing-based API",
    version="0.1.0",
)

# Register extensions
labthing.register_extension(example_extension)

# Attach an instance of our component
labthing.add_component(MyComponent(), "org.labthings.example.mycomponent")

# Add routes for the API views we created
labthing.add_view(DenoiseProperty, "/denoise")
labthing.add_view(QuickDataProperty, "/quick-data")


# Start the app
if __name__ == "__main__":
    from labthings.server.wsgi import Server

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    server = Server(app)
    server.run()
