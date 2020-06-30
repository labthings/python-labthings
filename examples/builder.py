# Monkey patch for easy concurrency
from labthings.server.monkey import patch_all

patch_all()

# Import requirements
import logging

from labthings.server.quick import create_app
from labthings.server import semantics
from labthings.server import fields

from components.pdf_component import PdfComponent


# Create LabThings Flask app
app, labthing = create_app(
    __name__,
    title="My Lab Device API",
    description="Test LabThing-based API",
    version="0.1.0",
    types=["org.labthings.examples.builder"],
)

# Attach an instance of our component
# Usually a Python object controlling some piece of hardware
my_component = PdfComponent()
labthing.add_component(my_component, "org.labthings.example.mycomponent")

# Make some properties and actions out of our component

labthing.build_property(
    my_component,  # Python object
    "magic_denoise",  # Objects attribute name
    "/denoise",  # URL to bind the property to
    description="A magic denoise property",
    semtype=semantics.moz.LevelProperty(100, 500, example=200),
)

labthing.build_property(
    my_component,  # Python object
    "magic_dictionary",  # Objects attribute name
    "/dictionary",  # URL to bind the property to
    description="A big dictionary of little properties",
    schema={  # Property is a dictionary, with these value types
        "voltage": fields.Int(),
        "volume": fields.List(fields.Int()),
        "mode": fields.String(),
        "light_on": fields.Bool(),
        "user": {"name": fields.String(), "id": fields.Int()},
        "bytes": fields.Bytes(),
    },
)

labthing.build_action(
    my_component.average_data,  # Python function
    "/average",  # URL to bind the action to
    description="Take an averaged measurement",
    safe=True,  # Is the state of the Thing unchanged by calling the action?
    idempotent=True,  # Can the action be called repeatedly with the same result?,
    args={  # How do we convert from the request input to function arguments?
        "n": fields.Int(description="Number of averages to take", example=5, default=5)
    },
)


# Start the app
if __name__ == "__main__":
    from labthings.server.wsgi import Server

    Server(app).run()
