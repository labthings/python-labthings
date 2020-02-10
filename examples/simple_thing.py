import random
import math
import time

from labthings.server.quick import create_app
from labthings.server.decorators import (
    ThingAction,
    ThingProperty,
    PropertySchema,
    use_args,
    marshal_task,
)
from labthings.server.view import View
from labthings.server.find import find_component
from labthings.server import fields
from labthings.core.tasks import taskify


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

    def average_data(self, n: int):
        """
        Average n-sets of data. Emulates a measurement that may take a while.
        """
        summed_data = self.data

        for i in range(n):
            summed_data = [summed_data[i] + el for i, el in enumerate(self.data)]
            time.sleep(0.25)

        summed_data = [i / n for i in summed_data]

        return summed_data


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


"""
Create a view to start an averaged measurement, and register is as a Thing action
"""


@ThingAction
class MeasurementAction(View):
    # Expect JSON parameters in the request body. Pass to post function as dictionary argument.
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
    app.run(host="0.0.0.0", port="5000", threaded=True, debug=True, use_reloader=False)
