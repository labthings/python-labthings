Quickstart
==========

The easiest way to get started with Python-LabThings is via the :meth:`labthings.create_app` function, and the :class:`labthings.LabThing` builder methods.

We will assume that for basic usage you already have some basic instrument control code. In our example, this is in the form of a ``PretendSpectrometer`` class, which will generate some data like your instrument control code might. Our ``PretendSpectrometer`` class has a ``data`` attribute which quickly returns a spectrum, an ``x_range`` attribute which determines the range of data we'll return, an ``integration_time`` attribute for cleaning up our signal, and a slow ``average_data(n)`` method to average ``n`` individual data measurements.

Building an API from this class requires a few extra considerations. In order to tell our API what data to expect from users, we need to construct a schema for each of our interactions. This schema simply maps variable names to JSON-compatible types, and is made simple via the :mod:`labthings.fields` module. 

For properties, the input and output MUST be formatted the same, and so a single ``schema`` argument handles both. For actions, the input parameters and output response may be different. In this case, we can pass a ``schema`` argument to format the output, and an ``args`` argument to specify the input parameters,

An example Lab Thing built from our ``PretendSpectrometer`` class, complete with schemas, might look like:


.. code-block:: python

    import time

    from labthings import ActionView, PropertyView, create_app, fields, find_component, op
    from labthings.example_components import PretendSpectrometer
    from labthings.json import encode_json

    """
    Class for our lab component functionality. This could include serial communication,
    equipment API calls, network requests, or a "virtual" device as seen here.
    """


    """
    Create a view to view and change our integration_time value,
    and register is as a Thing property
    """


    # Wrap in a semantic annotation to autmatically set schema and args
    class DenoiseProperty(PropertyView):
        """Value of integration_time"""

        schema = fields.Int(required=True, minimum=100, maximum=500)
        semtype = "LevelProperty"

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


Once started, the app will build and serve a full web API, and generate the following Thing Description:

.. code-block:: json

    {
        "@context": [
            "https://www.w3.org/2019/wot/td/v1",
            "https://iot.mozilla.org/schemas/"
        ],
        "id": "http://127.0.0.1:7486/",
        "base": "http://127.0.0.1:7486/",
        "title": "My PretendSpectrometer API",
        "description": "LabThing API for PretendSpectrometer",
        "properties": {
            "pretendSpectrometerData": {
                "title": "PretendSpectrometer_data",
                "description": "A single-shot measurement",
                "readOnly": true,
                "links": [{
                    "href": "/properties/PretendSpectrometer/data"
                }],
                "forms": [{
                    "op": "readproperty",
                    "htv:methodName": "GET",
                    "href": "/properties/PretendSpectrometer/data",
                    "contentType": "application/json"
                }],
                "type": "array",
                "items": {
                    "type": "number",
                    "format": "decimal"
                }
            },
            "pretendSpectrometerMagicDenoise": {
                "title": "PretendSpectrometer_magic_denoise",
                "description": "Single-shot integration time",
                "links": [{
                    "href": "/properties/PretendSpectrometer/magic_denoise"
                }],
                "forms": [{
                        "op": "readproperty",
                        "htv:methodName": "GET",
                        "href": "/properties/PretendSpectrometer/magic_denoise",
                        "contentType": "application/json"
                    },
                    {
                        "op": "writeproperty",
                        "htv:methodName": "PUT",
                        "href": "/properties/PretendSpectrometer/magic_denoise",
                        "contentType": "application/json"
                    }
                ],
                "type": "number",
                "format": "integer",
                "min": 100,
                "max": 500,
                "example": 200
            }
        },
        "actions": {
            "averageDataAction": {
                "title": "average_data_action",
                "description": "Take an averaged measurement",
                "links": [{
                    "href": "/actions/PretendSpectrometer/average_data"
                }],
                "forms": [{
                    "op": "invokeaction",
                    "htv:methodName": "POST",
                    "href": "/actions/PretendSpectrometer/average_data",
                    "contentType": "application/json"
                }],
                "input": {
                    "type": "object",
                    "properties": {
                        "n": {
                            "type": "number",
                            "format": "integer",
                            "default": 5,
                            "description": "Number of averages to take",
                            "example": 5
                        }
                    }
                }
            }
        },
        "links": [],
        "securityDefinitions": {},
        "security": "nosec_sc"
    }


For completeness of the examples, our ``PretendSpectrometer`` class code is:

.. code-block:: python

    import random
    import math
    import time

    class PretendSpectrometer:
        def __init__(self):
            self.x_range = range(-100, 100)
            self.integration_time = 200

        def make_spectrum(self, x, mu=0.0, sigma=25.0):
            """
            Generate a noisy gaussian function (to act as some pretend data)
            
            Our noise is inversely proportional to self.integration_time
            """
            x = float(x - mu) / sigma
            return (
                math.exp(-x * x / 2.0) / math.sqrt(2.0 * math.pi) / sigma
                + (1 / self.integration_time) * random.random()
            )

        @property
        def data(self):
            """Return a 1D data trace."""
            time.sleep(self.integration_time / 1000)
            return [self.make_spectrum(x) for x in self.x_range]

        def average_data(self, n: int):
            """Average n-sets of data. Emulates a measurement that may take a while."""
            summed_data = self.data

            for _ in range(n):
                summed_data = [summed_data[i] + el for i, el in enumerate(self.data)]
                time.sleep(0.25)

            summed_data = [i / n for i in summed_data]

            return summed_data
