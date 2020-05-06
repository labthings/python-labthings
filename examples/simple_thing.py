#!/usr/bin/env python
from gevent import monkey

# Patch most system modules. Leave threads untouched so we can still use them normally if needed.
print("Monkey patching with Gevenet")
monkey.patch_all(thread=False)
print("Monkey patching successful")

import random
import math
import time
import logging
import atexit

from labthings.server.quick import create_app
from labthings.server.decorators import (
    PropertySchema,
    use_args,
    marshal_with,
)
from labthings.server.schema import FieldSchema
from labthings.server.view import View, ActionView, PropertyView
from labthings.server.find import find_component
from labthings.server import fields
from labthings.core.tasks import taskify, update_task_data


"""
Class for our lab component functionality. This could include serial communication,
equipment API calls, network requests, or a "virtual" device as seen here.
"""


from gevent.monkey import get_original

get_ident = get_original("_thread", "get_ident")


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
        """Return a 1D data trace."""
        return [self.noisy_pdf(x) for x in self.x_range]

    def average_data(self, n: int):
        """Average n-sets of data. Emulates a measurement that may take a while."""
        summed_data = self.data

        logging.warning("Starting an averaged measurement. This may take a while...")
        for _ in range(n):
            summed_data = [summed_data[i] + el for i, el in enumerate(self.data)]
            time.sleep(0.1)

        summed_data = [i / n for i in summed_data]

        return summed_data


"""
Create a view to view and change our magic_denoise value,
and register is as a Thing property
"""


# Define the data we're going to output (get), and what to expect in (post)
@PropertySchema(
    fields.Integer(
        required=True,
        example=200,
        minimum=100,
        maximum=500,
        description="Value of magic_denoise",
    )
)
class DenoiseProperty(PropertyView):

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


@PropertySchema(fields.List(fields.Float()))
class QuickDataProperty(PropertyView):
    # Main function to handle GET requests
    def get(self):
        """Show the current data value"""

        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")
        return my_component.data


"""
Create a view to start an averaged measurement, and register is as a Thing action
"""


class MeasurementAction(ActionView):
    # Expect JSON parameters in the request body.
    # Pass to post function as dictionary argument.
    @use_args(
        {
            "averages": fields.Integer(
                missing=20,
                example=20,
                description="Number of data sets to average over",
            )
        }
    )
    # Output schema
    @marshal_with(FieldSchema(fields.List(fields.Number)))
    # Main function to handle POST requests
    def post(self, args):
        """Start an averaged measurement"""

        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")

        # Get arguments and start a background task
        n_averages = args.get("averages")

        # Return the task information
        return my_component.average_data(n_averages)


# Handle exit cleanup
def cleanup():
    logging.info("Exiting. Running any cleanup code here...")


atexit.register(cleanup)

# Create LabThings Flask app
app, labthing = create_app(
    __name__,
    prefix="/api",
    title=f"My Lab Device API",
    description="Test LabThing-based API",
    version="0.1.0",
)

# Attach an instance of our component
labthing.add_component(MyComponent(), "org.labthings.example.mycomponent")

# Add routes for the API views we created
labthing.add_view(DenoiseProperty, "/denoise")
labthing.add_view(QuickDataProperty, "/quick-data")
labthing.add_view(MeasurementAction, "/actions/measure")


# Start the app
if __name__ == "__main__":
    from labthings.server.wsgi import Server

    Server(app).run()
