from flask import Flask
from flask_cors import CORS

from .labthing import LabThing
from .exceptions import JSONExceptionHandler


def create_app(
    import_name,
    prefix: str = "/api",
    title: str = "",
    description: str = "",
    version: str = "0.0.0",
    handle_errors: bool = True,
    handle_cors: bool = True,
    flask_kwargs: dict = None,
):
    """QUick-create a LabThings-enabled Flask app
    
    Args:
        import_name: Flask import name. Usually `__name__`.
        prefix (str, optional): URL prefix for all LabThings views. Defaults to "/api".
        title (str, optional): Title/name of the LabThings Thing.
        description (str, optional): Brief description of the LabThings Thing.
        version (str, optional): Version number/code of the Thing. Defaults to "0.0.0".
        handle_errors (bool, optional): Use the LabThings error handler,
            to JSON format internal exceptions. Defaults to True.
        handle_cors (bool, optional): Automatically enable CORS on all LabThings views.
            Defaults to True.
        flask_kwargs (dict, optional): Keyword arguments to pass to the Flask instance.
    
    Returns:
        (Flask app object, LabThings object)
    """
    # Handle arguments
    if flask_kwargs is None:
        flask_kwargs = {}

    # Create Flask app
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
