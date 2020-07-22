# python-labthings

[![LabThings](https://img.shields.io/badge/-LabThings-8E00FF?style=flat&logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4NCjwhRE9DVFlQRSBzdmcgIFBVQkxJQyAnLS8vVzNDLy9EVEQgU1ZHIDEuMS8vRU4nICAnaHR0cDovL3d3dy53My5vcmcvR3JhcGhpY3MvU1ZHLzEuMS9EVEQvc3ZnMTEuZHRkJz4NCjxzdmcgY2xpcC1ydWxlPSJldmVub2RkIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIHN0cm9rZS1taXRlcmxpbWl0PSIyIiB2ZXJzaW9uPSIxLjEiIHZpZXdCb3g9IjAgMCAxNjMgMTYzIiB4bWw6c3BhY2U9InByZXNlcnZlIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwYXRoIGQ9Im0xMjIuMjQgMTYyLjk5aDQwLjc0OHYtMTYyLjk5aC0xMDEuODd2NDAuNzQ4aDYxLjEyMnYxMjIuMjR6IiBmaWxsPSIjZmZmIi8+PHBhdGggZD0ibTAgMTIuMjI0di0xMi4yMjRoNDAuNzQ4djEyMi4yNGg2MS4xMjJ2NDAuNzQ4aC0xMDEuODd2LTEyLjIyNGgyMC4zNzR2LTguMTVoLTIwLjM3NHYtOC4xNDloOC4wMTl2LTguMTVoLTguMDE5di04LjE1aDIwLjM3NHYtOC4xNDloLTIwLjM3NHYtOC4xNWg4LjAxOXYtOC4xNWgtOC4wMTl2LTguMTQ5aDIwLjM3NHYtOC4xNWgtMjAuMzc0di04LjE0OWg4LjAxOXYtOC4xNWgtOC4wMTl2LTguMTVoMjAuMzc0di04LjE0OWgtMjAuMzc0di04LjE1aDguMDE5di04LjE0OWgtOC4wMTl2LTguMTVoMjAuMzc0di04LjE1aC0yMC4zNzR6IiBmaWxsPSIjZmZmIi8+PC9zdmc+DQo=)](https://github.com/labthings/)
[![ReadTheDocs](https://readthedocs.org/projects/python-labthings/badge/?version=latest&style=flat)](https://python-labthings.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/labthings)](https://pypi.org/project/labthings/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/labthings/python-labthings/branch/master/graph/badge.svg)](https://codecov.io/gh/labthings/python-labthings)
[![Riot.im](https://img.shields.io/badge/chat-on%20riot.im-368BD6)](https://riot.im/app/#/room/#labthings:matrix.org)

A Python implementation of the LabThings API structure, based on the Flask microframework.

## Installation

`pip install labthings`

## Quickstart example

This example assumes a `PretendSpectrometer` class, which already has `data` and `integration_time` attributes, as well as an `average_data(n)` method. LabThings allows you to easily convert this existing instrument control code into a fully documented, standardised web API complete with auto-discovery and automatic background task threading.

```python
from labthings import fields, create_app
from labthings.example_components import PretendSpectrometer


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

# Integration time property
labthing.build_property(
    my_spectrometer,  # Python object
    "integration_time",  # Objects attribute name
    description="Single-shot integration time",
    schema=fields.Int(min=100, max=500, example=200, unit="microsecond")
)

# Averaged measurement action
labthing.build_action(
    my_spectrometer,  # Python object
    "average_data",  # Objects method name
    description="Take an averaged measurement",
    schema=fields.List(fields.Number()),
    args={  # How do we convert from the request input to function arguments?
        "n": fields.Int(description="Number of averages to take", example=5, default=5)
    },
)


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
