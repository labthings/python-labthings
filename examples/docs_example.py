from labthings import fields, create_app
from labthings.example_components import PretendSpectrometer


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

# Integration time property
labthing.build_property(
    my_spectrometer,  # Python object
    "integration_time",  # Objects attribute name
    description="A magic denoise property",
    schema=fields.Int(min=100, max=500, example=200, unit="microsecond"),
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
