import random
import math
import time


class PretendSpectrometer:
    def __init__(self):
        self.x_range = range(-100, 100)
        self.integration_time = 200
        self.settings = {
            "voltage": 5,
            "mode": "spectrum",
            "light_on": True,
            "user": {"name": "Squidward", "id": 1},
        }

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
