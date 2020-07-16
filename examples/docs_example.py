from labthings.server.quick import create_app
from labthings.server import fields

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


# Create LabThings Flask app
app, labthing = create_app(
    __name__,
    title="My PretendSpectrometer API",
    description="LabThing API for PretendSpectrometer",
    version="0.1.0",
)


# Make some properties and actions out of our component
my_spectrometer = PretendSpectrometer()

# Single-shot data property
labthing.build_property(
    my_spectrometer,  # Python object
    "data",  # Objects attribute name
    description="A single-shot measurement",
    readonly=True,
    schema=fields.List(fields.Number()),
)

# Magic denoise property
labthing.build_property(
    my_spectrometer,  # Python object
    "magic_denoise",  # Objects attribute name
    description="A magic denoise property",
    schema=fields.Int(min=100, max=500, example=200),
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
