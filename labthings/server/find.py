import logging
from flask import current_app

from . import EXTENSION_NAME


def current_labthing():
    app = current_app._get_current_object()  # skipcq: PYL-W0212
    if not app:
        return None
    logging.debug("Active app extensions:")
    logging.debug(app.extensions)
    logging.debug("Active labthing:")
    logging.debug(app.extensions[EXTENSION_NAME])
    return app.extensions[EXTENSION_NAME]


def registered_extensions(labthing_instance=None):
    if not labthing_instance:
        labthing_instance = current_labthing()
    return labthing_instance.extensions


def registered_components(labthing_instance=None):
    if not labthing_instance:
        labthing_instance = current_labthing()
    return labthing_instance.components


def find_component(device_name, labthing_instance=None):
    if not labthing_instance:
        labthing_instance = current_labthing()

    if device_name in labthing_instance.components:
        return labthing_instance.components[device_name]
    else:
        return None


def find_extension(extension_name, labthing_instance=None):
    if not labthing_instance:
        labthing_instance = current_labthing()

    logging.debug("Current labthing:")
    logging.debug(current_labthing())

    if extension_name in labthing_instance.extensions:
        return labthing_instance.extensions[extension_name]
    else:
        return None
