import logging
from flask import current_app, url_for
import weakref

from .names import EXTENSION_NAME

__all__ = [
    "current_app",
    "url_for",
    "current_labthing",
    "registered_extensions",
    "registered_components",
    "find_component",
    "find_extension",
]


def current_labthing(app=None):
    """The LabThing instance handling current requests.
    
    Searches for a valid LabThing extension attached to the current Flask context.

    :param app:  (Default value = None)

    """
    # We use _get_current_object so that Task threads can still
    # reach the Flask app object. Just using current_app returns
    # a wrapper, which breaks it's use in Task threads
    try:
        app = current_app._get_current_object()  # skipcq: PYL-W0212
    except RuntimeError:
        return None
    ext = app.extensions.get(EXTENSION_NAME, None)
    if isinstance(ext, weakref.ref):
        return ext()
    else:
        return ext


def registered_extensions(labthing_instance=None):
    """Find all LabThings Extensions registered to a LabThing instance

    :param labthing_instance: LabThing instance to search for extensions.
            Defaults to current_labthing.
    :type labthing_instance: optional
    :returns: LabThing Extension objects
    :rtype: list

    """
    if not labthing_instance:
        labthing_instance = current_labthing()

    return getattr(labthing_instance, "extensions", {})


def registered_components(labthing_instance=None):
    """Find all LabThings Components registered to a LabThing instance

    :param labthing_instance: LabThing instance to search for extensions.
            Defaults to current_labthing.
    :type labthing_instance: optional
    :returns: Python objects registered as LabThings components
    :rtype: list

    """
    if not labthing_instance:
        labthing_instance = current_labthing()
    return labthing_instance.components


def find_component(component_name, labthing_instance=None):
    """Find a particular LabThings Component registered to a LabThing instance

    :param component_name: Fully qualified name of the component
    :type component_name: str
    :param labthing_instance: LabThing instance to search for the component.
            Defaults to current_labthing.
    :type labthing_instance: optional
    :returns: Python object registered as a component, or `None` if not found

    """
    if not labthing_instance:
        labthing_instance = current_labthing()

    if component_name in labthing_instance.components:
        return labthing_instance.components[component_name]
    else:
        return None


def find_extension(extension_name, labthing_instance=None):
    """Find a particular LabThings Extension registered to a LabThing instance

    :param extension_name: Fully qualified name of the extension
    :type extension_name: str
    :param labthing_instance: LabThing instance to search for the extension.
            Defaults to current_labthing.
    :type labthing_instance: optional
    :returns: LabThings Extension object, or `None` if not found

    """
    if not labthing_instance:
        labthing_instance = current_labthing()

    if extension_name in labthing_instance.extensions:
        return labthing_instance.extensions[extension_name]
    else:
        return None
