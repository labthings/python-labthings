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
    """Quick-create a LabThings-enabled Flask app

    :param import_name: Flask import name. Usually ``__name__``.
    :param prefix: URL prefix for all LabThings views. Defaults to "/api".
    :type prefix: str
    :param title: Title/name of the LabThings Thing.
    :type title: str
    :param description: Brief description of the LabThings Thing.
    :type description: str
    :param version: Version number/code of the Thing. Defaults to "0.0.0".
    :type version: str
    :param handle_errors: Use the LabThings error handler,
            to JSON format internal exceptions. Defaults to True.
    :type handle_errors: bool
    :param handle_cors: Automatically enable CORS on all LabThings views.
            Defaults to True.
    :type handle_cors: bool
    :param flask_kwargs: Keyword arguments to pass to the Flask instance.
    :type flask_kwargs: dict
    :param prefix: str:  (Default value = "")
    :param title: str:  (Default value = "")
    :param description: str:  (Default value = "")
    :param types: list:  (Default value = None)
    :param version: str:  (Default value = "0.0.0")
    :param handle_errors: bool:  (Default value = True)
    :param handle_cors: bool:  (Default value = True)
    :param flask_kwargs: dict:  (Default value = None)
    :returns: (Flask app object, LabThings object)

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
