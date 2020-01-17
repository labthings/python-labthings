from flask import Flask
from flask_cors import CORS

from .labthing import LabThing
from .exceptions import JSONExceptionHandler


def create_app(
    import_name,
    prefix: str = "",
    title: str = "",
    description: str = "",
    version: str = "0.0.0",
    handle_errors: bool = True,
    handle_cors: bool = True,
    flask_kwargs: dict = {},
):
    app = Flask(import_name, **flask_kwargs)
    app.url_map.strict_slashes = False

    # Handle CORS
    if handle_cors:
        cors_handler = CORS(app, resources=f"{prefix}/*")

    # Handle errors
    if handle_errors:
        error_handler = JSONExceptionHandler()
        error_handler.init_app(app)

    # Create a LabThing
    labthing = LabThing(
        app, prefix=prefix, title=title, description=description, version=str(version)
    )

    # Store references to added-in handlers
    if cors_handler:
        labthing.handlers["cors"] = cors_handler
    if error_handler:
        labthing.handlers["error"] = error_handler

    return app, labthing
