import random
import math
import time

from typing import List

"""
Class for our lab component functionality. This could include serial communication,
equipment API calls, network requests, or a "virtual" device as seen here.
"""


class PdfComponent:
    def __init__(self):
        self.x_range = range(-100, 100)
        self.magic_denoise = 200

        self.magic_dictionary = {
            "voltage": 5,
            "volume": [5, 10],
            "mode": "spectrum",
            "light_on": True,
            "user": {"name": "Squidward", "id": 1},
        }

    def noisy_pdf(self, x, mu=0.0, sigma=25.0):
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
        return [self.noisy_pdf(x) for x in self.x_range]

    def average_data(self, n: int = 10, optlist: List[int] = None):
        """Average n-sets of data. Emulates a measurement that may take a while."""
        if optlist is None:
            optlist = [1, 2, 3]
        summed_data = self.data

        for i in range(n):
            summed_data = [summed_data[i] + el for i, el in enumerate(self.data)]
            time.sleep(0.25)

        summed_data = [i / n for i in summed_data]

        return summed_data
