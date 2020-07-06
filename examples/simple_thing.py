#!/usr/bin/env python
from labthings import monkey

monkey.patch_all()

import random
import math
import time
import logging
import atexit

from labthings.server.quick import create_app
from labthings.server import semantics
from labthings.server.view import ActionView, PropertyView
from labthings.server.find import find_component
from labthings.server import fields


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


# Wrap in a semantic annotation to autmatically set schema and args
@semantics.moz.LevelProperty(100, 500, example=200)
class DenoiseProperty(PropertyView):
    """Value of magic_denoise"""

    def get(self):
        # When a GET request is made, we'll find our attached component
        my_component = find_component("org.labthings.example.mycomponent")
        return my_component.magic_denoise

    def put(self, new_property_value):
        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")

        # Apply the new value
        my_component.magic_denoise = new_property_value

        return my_component.magic_denoise


"""
Create a view to quickly get some noisy data, and register is as a Thing property
"""


class QuickDataProperty(PropertyView):
    """Show the current data value"""

    # Marshal the response as a list of floats
    schema = fields.List(fields.Float())

    def get(self):
        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")
        return my_component.data


"""
Create a view to start an averaged measurement, and register is as a Thing action
"""


class MeasurementAction(ActionView):
    # Expect JSON parameters in the request body.
    # Pass to post function as dictionary argument.
    args = {
        "averages": fields.Integer(
            missing=20, example=20, description="Number of data sets to average over",
        )
    }
    # Marshal the response as a list of numbers
    schema = fields.List(fields.Number)

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
