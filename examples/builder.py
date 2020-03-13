import uuid
import types
import functools
import atexit
import logging

from labthings.server.quick import create_app, property_of

from components.pdf_component import PdfComponent


def cleanup():
    logging.info("Exiting. Running any cleanup code here...")


# Create LabThings Flask app
app, labthing = create_app(
    __name__,
    prefix="/api",
    title="My Lab Device API",
    description="Test LabThing-based API",
    version="0.1.0",
)

# Attach an instance of our component
# Usually a Python object controlling some piece of hardware
my_component = PdfComponent()
labthing.add_component(my_component, "org.labthings.example.mycomponent")

# Add routes for the API views we created
labthing.add_view(
    property_of(my_component, "magic_denoise", description="A magic denoise property"),
    "/denoise",
)
labthing.add_view(
    property_of(
        my_component,
        "magic_dictionary",
        description="A big dictionary of little properties",
    ),
    "/dictionary",
)

atexit.register(cleanup)

# Start the app
if __name__ == "__main__":
    from labthings.server.wsgi import Server

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    server = Server(app)
    server.run(host="0.0.0.0", port=5000, debug=False)
