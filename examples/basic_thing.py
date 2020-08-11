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
    title=f"My Lab Device API",
    description="Test LabThing-based API",
    version="0.1.0",
)


# Add routes for the API views we created
labthing.add_property(
    Property(
        "integration_time",
        writeproperty=lambda x: setattr(my_spectrometer, "integration_time", x),
        readproperty=lambda: getattr(my_spectrometer, "integration_time"),
        semtype=semantics.moz.LevelProperty(100, 500, example=200),
    )
)

labthing.add_property(
    Property(
        "quick-data",
        readproperty=lambda: getattr(my_spectrometer, "data"),
        schema=fields.List(fields.Float()),
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
        schema=fields.List(fields.Number),
    )
)


# Start the app
if __name__ == "__main__":
    from labthings import Server

    Server(app).run()
