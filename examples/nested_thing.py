import random
import math
import uuid
import logging

from labthings.server.quick import create_app
from labthings.server.view import PropertyView
from labthings.server.find import find_component
from labthings.server.schema import Schema
from labthings.server import fields


"""
Class for our lab component functionality. This could include serial communication,
equipment API calls, network requests, or a "virtual" device as seen here.
"""


class DataSet:
    def __init__(self, x_values, y_values):
        self.xs = x_values
        self.ys = y_values


class DataSetSchema(Schema):
    xs = fields.List(fields.Number())
    ys = fields.List(fields.Number())


class MyComponent:
    def __init__(self):
        self.id = uuid.uuid4()  # skipcq: PYL-C0103
        self.x_range = range(-100, 100)
        self.magic_denoise = 200

    def noisy_pdf(self, x_value, mu=0.0, sigma=25.0):
        """
        Generate a noisy gaussian function (to act as some pretend data)
        
        Our noise is inversely proportional to self.magic_denoise
        """
        x_value = float(x_value - mu) / sigma
        return (
            math.exp(-x_value * x_value / 2.0) / math.sqrt(2.0 * math.pi) / sigma
            + (1 / self.magic_denoise) * random.random()
        )

    @property
    def data(self):
        """Return a 1D data trace."""
        return DataSet(self.x_range, [self.noisy_pdf(x) for x in self.x_range])


class MyComponentSchema(Schema):
    id = fields.UUID()
    magic_denoise = fields.Int()
    data = fields.Nested(DataSetSchema())


"""
Create a view to view and change our magic_denoise value,
and register is as a Thing property
"""


class DenoiseProperty(PropertyView):

    schema = fields.Integer(
        required=True,
        example=200,
        minimum=100,
        maximum=500,
        description="Value of magic_denoise",
    )

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


class MyComponentProperty(PropertyView):
    # Main function to handle GET requests

    schema = MyComponentSchema()

    def get(self):
        """Show the current data value"""

        # Find our attached component
        return find_component("org.labthings.example.mycomponent")


# Create LabThings Flask app
app, labthing = create_app(
    __name__,
    prefix="/api",
    title="My Lab Device API",
    description="Test LabThing-based API",
    version="0.1.0",
)

# Attach an instance of our component
labthing.add_component(MyComponent(), "org.labthings.example.mycomponent")

# Add routes for the API views we created
labthing.add_view(DenoiseProperty, "/denoise")
labthing.add_view(MyComponentProperty, "/component")


# Start the app
if __name__ == "__main__":
    from labthings.server.wsgi import Server

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    server = Server(app)
    server.run()
