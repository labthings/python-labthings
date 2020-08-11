from labthings import create_app, semantics, fields
from labthings.example_components import PretendSpectrometer


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
my_spectrometer = PretendSpectrometer()
labthing.add_component(my_spectrometer, "org.labthings.example.mycomponent")

# Make some properties and actions out of our component

labthing.build_property(
    my_spectrometer,  # Python object
    "integration_time",  # Objects attribute name
    description="Single-shot integration time",
    semtype=semantics.moz.LevelProperty(100, 500, example=200, unit="microsecond"),
)

labthing.build_property(
    my_spectrometer,  # Python object
    "settings",  # Objects attribute name
    description="A big dictionary of little settings",
    schema={  # Property is a dictionary, with these value types
        "voltage": fields.Int(),
        "mode": fields.String(),
        "light_on": fields.Bool(),
        "user": {"name": fields.String(), "id": fields.Int()},
    },
)

labthing.build_action(
    my_spectrometer,  # Python object
    "average_data",  # Objects method name
    description="Take an averaged measurement",
    safe=True,  # Is the state of the Thing unchanged by calling the action?
    idempotent=True,  # Can the action be called repeatedly with the same result?,
    args={  # How do we convert from the request input to function arguments?
        "n": fields.Int(description="Number of averages to take", example=5, default=5)
    },
)

# Start the app
if __name__ == "__main__":
    from labthings import Server

    Server(app).run()
