# Monkey patch for easy concurrency
from labthings.server.monkey import patch_all

patch_all()

# Import requirements
import logging

from labthings.server.quick import create_app

from components.pdf_component import PdfComponent


# Create LabThings Flask app
app, labthing = create_app(
    __name__,
    prefix="/api",
    title="My Lab Device API",
    description="Test LabThing-based API",
    version="0.1.0",
    types=["org.labthings.examples.builder"],
)

# Attach an instance of our component
# Usually a Python object controlling some piece of hardware
my_component = PdfComponent()
labthing.add_component(my_component, "org.labthings.example.mycomponent")

# Add routes for the API views we created

labthing.build_property(
    my_component, "magic_denoise", "/denoise", description="A magic denoise property",
)

labthing.build_property(
    my_component,
    "magic_dictionary",
    "/dictionary",
    description="A big dictionary of little properties",
)

labthing.build_action(
    my_component.average_data,
    "/average",
    description="Take an averaged measurement",
    safe=True,  # Is the state of the Thing unchanged by calling the action?
    idempotent=True,  # Can the action be called repeatedly with the same result?
)


# Start the app
if __name__ == "__main__":
    from labthings.server.wsgi import Server

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    server = Server(app)
    server.run()
