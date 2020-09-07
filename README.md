# Python LabThings (for Flask)

[![LabThings](https://img.shields.io/badge/-LabThings-8E00FF?style=flat&logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4NCjwhRE9DVFlQRSBzdmcgIFBVQkxJQyAnLS8vVzNDLy9EVEQgU1ZHIDEuMS8vRU4nICAnaHR0cDovL3d3dy53My5vcmcvR3JhcGhpY3MvU1ZHLzEuMS9EVEQvc3ZnMTEuZHRkJz4NCjxzdmcgY2xpcC1ydWxlPSJldmVub2RkIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIHN0cm9rZS1taXRlcmxpbWl0PSIyIiB2ZXJzaW9uPSIxLjEiIHZpZXdCb3g9IjAgMCAxNjMgMTYzIiB4bWw6c3BhY2U9InByZXNlcnZlIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwYXRoIGQ9Im0xMjIuMjQgMTYyLjk5aDQwLjc0OHYtMTYyLjk5aC0xMDEuODd2NDAuNzQ4aDYxLjEyMnYxMjIuMjR6IiBmaWxsPSIjZmZmIi8+PHBhdGggZD0ibTAgMTIuMjI0di0xMi4yMjRoNDAuNzQ4djEyMi4yNGg2MS4xMjJ2NDAuNzQ4aC0xMDEuODd2LTEyLjIyNGgyMC4zNzR2LTguMTVoLTIwLjM3NHYtOC4xNDloOC4wMTl2LTguMTVoLTguMDE5di04LjE1aDIwLjM3NHYtOC4xNDloLTIwLjM3NHYtOC4xNWg4LjAxOXYtOC4xNWgtOC4wMTl2LTguMTQ5aDIwLjM3NHYtOC4xNWgtMjAuMzc0di04LjE0OWg4LjAxOXYtOC4xNWgtOC4wMTl2LTguMTVoMjAuMzc0di04LjE0OWgtMjAuMzc0di04LjE1aDguMDE5di04LjE0OWgtOC4wMTl2LTguMTVoMjAuMzc0di04LjE1aC0yMC4zNzR6IiBmaWxsPSIjZmZmIi8+PC9zdmc+DQo=)](https://github.com/labthings/)
[![ReadTheDocs](https://readthedocs.org/projects/python-labthings/badge/?version=latest&style=flat)](https://python-labthings.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/labthings)](https://pypi.org/project/labthings/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/labthings/python-labthings/branch/master/graph/badge.svg)](https://codecov.io/gh/labthings/python-labthings)
[![Riot.im](https://img.shields.io/badge/chat-on%20riot.im-368BD6)](https://riot.im/app/#/room/#labthings:matrix.org)

A thread-based Python implementation of the LabThings API structure, based on the Flask microframework.

## Installation

`pip install labthings`

## Quickstart example

This example assumes a `PretendSpectrometer` class, which already has `data` and `integration_time` attributes, as well as an `average_data(n)` method. LabThings allows you to easily convert this existing instrument control code into a fully documented, standardised web API complete with auto-discovery and automatic background task threading.

```python
#!/usr/bin/env python
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
```

## Acknowledgements

Much of the code surrounding default response formatting has been liberally taken from [Flask-RESTful](https://github.com/flask-restful/flask-restful). The integrated [Marshmallow](https://github.com/marshmallow-code/marshmallow) support was inspired by [Flask-Marshmallow](https://github.com/marshmallow-code/flask-marshmallow) and [Flask-ApiSpec](https://github.com/jmcarp/flask-apispec). 

## Developer notes

### Changelog generation

* `npm install -g conventional-changelog-cli`
* `conventional-changelog -r 1 --config ./changelog.config.js -i CHANGELOG.md -s`
