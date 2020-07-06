from flask import Flask

from flask_cors import CORS

from .labthing import LabThing


def create_app(
    import_name,
    prefix: str = "",
    title: str = "",
    description: str = "",
    types: list = None,
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
    if types is None:
        types = []
    # Handle arguments
    if flask_kwargs is None:
        flask_kwargs = {}

    # Create Flask app
    app = Flask(import_name, **flask_kwargs)
    app.url_map.strict_slashes = False

    # Handle CORS
    if handle_cors:
        CORS(app, resources=f"{prefix}/*")

    # Create a LabThing
    labthing = LabThing(
        app,
        prefix=prefix,
        title=title,
        description=description,
        types=types,
        version=str(version),
        format_flask_exceptions=handle_errors,
    )

    return app, labthing
