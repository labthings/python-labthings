#!/usr/bin/env python
import time

from labthings import create_app, fields, find_component, semantics
from labthings.example_components import PretendSpectrometer
from labthings.json import encode_json
from labthings.views import ActionView, PropertyView, op

"""
Class for our lab component functionality. This could include serial communication,
equipment API calls, network requests, or a "virtual" device as seen here.
"""


"""
Create a view to view and change our integration_time value,
and register is as a Thing property
"""


# Wrap in a semantic annotation to autmatically set schema and args
@semantics.moz.LevelProperty(100, 500, example=200)
class DenoiseProperty(PropertyView):
    """Value of integration_time"""

    @op.readproperty
    def get(self):
        # When a GET request is made, we'll find our attached component
        my_component = find_component("org.labthings.example.mycomponent")
        return my_component.integration_time

    @op.writeproperty
    def put(self, new_property_value):
        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")

        # Apply the new value
        my_component.integration_time = new_property_value

        return my_component.integration_time

    @op.observeproperty
    def websocket(self, ws):
        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")
        initial_value = None
        while not ws.closed:
            time.sleep(1)
            if my_component.integration_time != initial_value:
                ws.send(encode_json(my_component.integration_time))
                initial_value = my_component.integration_time


"""
Create a view to quickly get some noisy data, and register is as a Thing property
"""


class QuickDataProperty(PropertyView):
    """Show the current data value"""

    # Marshal the response as a list of floats
    schema = fields.List(fields.Float())

    @op.readproperty
    def get(self):
        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")
        return my_component.data

    @op.observeproperty
    def websocket(self, ws):
        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")
        while not ws.closed:
            ws.send(encode_json(my_component.data))


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
    @op.invokeaction
    def post(self, args):
        """Start an averaged measurement"""

        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")

        # Get arguments and start a background task
        n_averages = args.get("averages")

        # Return the task information
        return my_component.average_data(n_averages)


# Create LabThings Flask app
app, labthing = create_app(
    __name__,
    title="My Lab Device API",
    description="Test LabThing-based API",
    version="0.1.0",
)

# Attach an instance of our component
# Usually a Python object controlling some piece of hardware
my_spectrometer = PretendSpectrometer()
labthing.add_component(my_spectrometer, "org.labthings.example.mycomponent")


# Add routes for the API views we created
labthing.add_view(DenoiseProperty, "/integration_time")
labthing.add_view(QuickDataProperty, "/quick-data")
labthing.add_view(MeasurementAction, "/actions/measure")


# Start the app
if __name__ == "__main__":
    from labthings import Server

    Server(app).run()
