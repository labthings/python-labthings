#!/usr/bin/env python
from labthings import (
    create_app,
    semantics,
    fields,
    Property,
    Action,
)
from labthings.example_components import PretendSpectrometer


my_spectrometer = PretendSpectrometer()


# Create LabThings Flask app
app, labthing = create_app(
    __name__,
    title="My Lab Device API",
    description="Test LabThing-based API",
    version="0.1.0",
)


# Add routes for the API views we created
labthing.add_property(
    Property(
        "my_spectrometer/integration_time",
        writeproperty=lambda x: setattr(my_spectrometer, "integration_time", x),
        readproperty=lambda: getattr(my_spectrometer, "integration_time"),
        description="Single-shot integration time",
        semtype=semantics.moz.LevelProperty(100, 500, example=200),
    )
)

labthing.add_property(
    Property(
        "my_spectrometer/quick-data",
        readproperty=lambda: getattr(my_spectrometer, "data"),
        schema=fields.List(fields.Float()),
    )
)

labthing.add_property(
    Property(
        "my_spectrometer/settings",
        writeproperty=lambda x: my_spectrometer.settings.update(x),
        readproperty=lambda: getattr(my_spectrometer, "settings"),
        description="A big dictionary of little settings",
        schema={  # Property is a dictionary, with these value types
            "voltage": fields.Int(),
            "mode": fields.String(),
            "light_on": fields.Bool(),
            "user": {"name": fields.String(), "id": fields.Int()},
        },
    )
)

labthing.add_action(
    Action(
        name="measure",
        invokeaction=lambda args: my_spectrometer.average_data(args.get("averages")),
        args={
            "averages": fields.Integer(
                missing=20,
                example=20,
                description="Number of data sets to average over",
            )
        },
        description="Take an averaged measurement",
        safe=True,  # Is the state of the Thing unchanged by calling the action?
        idempotent=True,  # Can the action be called repeatedly with the same result?,
        schema=fields.List(fields.Number),
    )
)


# Start the app
if __name__ == "__main__":
    from labthings import Server

    Server(app).run()
