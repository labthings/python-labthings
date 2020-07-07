from labthings import quick

from flask import Flask
from labthings.labthing import LabThing


def test_create_app():
    app, labthing = quick.create_app(__name__)
    assert isinstance(app, Flask)
    assert isinstance(labthing, LabThing)


def test_create_app_options():
    app, labthing = quick.create_app(
        __name__,
        types=["org.labthings.tests.labthing"],
        flask_kwargs={"static_url_path": "/static"},
        handle_cors=False,
    )
    assert isinstance(app, Flask)
    assert isinstance(labthing, LabThing)
