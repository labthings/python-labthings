Basic usage
===========

The easiest way to get started with Python-LabThings is via the :mod:`labthings.quick` module, and the :class:`labthings.LabThing` builder methods.

We will assume that for basic usage you already have some basic instrument control code. In our example, this is in the form of a ``PretendSpectrometer`` class, which will generate some data like your instrument control code might. Our ``PretendSpectrometer`` class has a ``data`` property which quickly returns a spectrum, an ``x_range`` property which determines the range of data we'll return, a ``magic_denoise`` property for cleaning up our signal, and a slow ``average_data(n)`` method to average ``n`` individual data measurements.

Building an API from this class requires a few extra considerations. In order to tell our API what data to expect from users, we need to construct a schema for each of our interactions. This schema simply maps variable names to JSON-compatible types, and is made simple via the :mod:`labthings.fields` module. 

For properties, the input and output MUST be formatted the same, and so a single ``schema`` argument handles both. For actions, the input parameters and output response may be different. In this case, we can pass a ``schema`` argument to format the output, and an ``args`` argument to specify the input parameters,

An example Lab Thing built from our ``PretendSpectrometer`` class, complete with schemas, might look like:


.. code-block:: python

    from labthings.server.quick import create_app
    from labthings import fields

    from my_components import PretendSpectrometer


    # Create LabThings Flask app
    app, labthing = create_app(
        __name__,
        title="My PretendSpectrometer API",
        description="LabThing API for PretendSpectrometer",
        version="0.1.0"
    )


    # Make some properties and actions out of our component
    my_spectrometer = PretendSpectrometer()

    # Single-shot data property
    labthing.build_property(
        my_spectrometer,  # Python object
        "data",  # Objects attribute name
        description="A single-shot measurement",
        readonly=True,
        schema=fields.List(fields.Number())
    )

    # Magic denoise property
    labthing.build_property(
        my_spectrometer,  # Python object
        "magic_denoise",  # Objects attribute name
        description="A magic denoise property",
        schema=fields.Int(min=100, max=500, example=200)
    )

    # Averaged measurement action
    labthing.build_action(
        my_spectrometer.average_data,  # Python function
        description="Take an averaged measurement",
        args={  # How do we convert from the request input to function arguments?
            "n": fields.Int(description="Number of averages to take", example=5, default=5)
        },
    )


    # Start the app
    if __name__ == "__main__":
        from labthings.server.wsgi import Server
        Server(app).run()


Once started, the app will build and serve a full web API, and generate the following Thing Description:

.. code-block:: JSON

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
                "description": "A magic denoise property",
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
        "links": [...],
        "securityDefinitions": {...},
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
            self.magic_denoise = 200

        def make_spectrum(self, x, mu=0.0, sigma=25.0):
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
            return [self.make_spectrum(x) for x in self.x_range]

        def average_data(self, n: int):
            """Average n-sets of data. Emulates a measurement that may take a while."""
            summed_data = self.data

            for _ in range(n):
                summed_data = [summed_data[i] + el for i, el in enumerate(self.data)]
                time.sleep(0.25)

            summed_data = [i / n for i in summed_data]

            return summed_data
