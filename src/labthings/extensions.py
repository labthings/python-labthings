import glob
import inspect
import logging
import os
import sys
import traceback
from importlib import util
from typing import Callable, Dict, List, Union

from flask import url_for

from .utilities import camel_to_snake, get_docstring, snake_to_spine
from .views import View as BaseView
from .views.builder import static_from


class BaseExtension:
    """Parent class for all extensions.

    Handles binding route views and forms.


    """

    def __init__(
        self,
        name: str,
        description="",
        version="0.0.0",
        static_url_path="/static",
        static_folder=None,
    ):
        self._views: dict = (
            {}
        )  # Key: Full, Python-safe ID. Val: Original rule, and view class
        self._rules: dict = {}  # Key: Original rule. Val: View class
        self._meta: dict = {}  # Extra metadata to add to the extension description

        self._on_registers: List[
            Union[Dict, Callable]
        ] = []  # List of dictionaries of functions to run on registration

        self._on_components: List[
            Union[Dict, Callable]
        ] = []  # List of dictionaries of functions to run as components are added

        self._cls = str(self)  # String description of extension instance

        self._name = name
        self.description = description or get_docstring(self)
        self.version = str(version)

        self.methods: Dict[str, Callable] = {}

        self.static_view_class = static_from(static_folder)
        self.add_view(
            self.static_view_class,
            f"{static_url_path}",
            f"{static_url_path}/<path:path>",
            endpoint="static",
        )

    @property
    def views(self):
        """ """
        return self._views

    @property
    def rules(self):
        return self._rules

    @property
    def on_components(self):
        return self._on_components

    @property
    def on_registers(self):
        return self._on_registers

    def add_view(self, view_class, *urls, endpoint=None, **kwargs):
        """

        :param view_class:
        :param *urls:
        :param endpoint:  (Default value = None)
        :param **kwargs:

        """
        # Remove all leading slashes from view route
        cleaned_urls = list(urls)
        for i, cleaned_url in enumerate(cleaned_urls):
            while cleaned_url and cleaned_urls[i][0] == "/":
                cleaned_urls[i] = cleaned_urls[i][1:]

        # Expand the rule to include extension name
        full_urls = [
            "/{}/{}".format(self._name_uri_safe, cleaned_url)
            for cleaned_url in cleaned_urls
        ]

        # Build endpoint if none given
        if not endpoint:
            endpoint = camel_to_snake(view_class.__name__)

        # Store route information in a dictionary
        d = {"urls": full_urls, "view": view_class, "kwargs": kwargs}

        # Add view to private views dictionary
        self._views[endpoint] = d
        # Store the rule expansion information
        for url in cleaned_urls:
            self._rules[url] = self._views[endpoint]

        # Store this extension name as the View owner
        if issubclass(view_class, BaseView):
            view_class.set_extension(self.name)

    def on_register(self, function, args=None, kwargs=None):
        """

        :param function:
        :param args:  (Default value = None)
        :param kwargs:  (Default value = None)

        """
        if not callable(function):
            raise TypeError("Function must be a callable")

        self._on_registers.append(
            {"function": function, "args": args or (), "kwargs": kwargs or {}}
        )

    def on_component(self, component_name: str, function, args=None, kwargs=None):
        """

        :param component_name: str:
        :param function:
        :param args:  (Default value = None)
        :param kwargs:  (Default value = None)

        """
        if not callable(function):
            raise TypeError("Function must be a callable")

        self._on_components.append(
            {
                "component": component_name,
                "function": function,
                "args": args or (),
                "kwargs": kwargs or {},
            }
        )

    @property
    def meta(self):
        """ """
        d = {}
        for k, v in self._meta.items():
            if callable(v):
                d[k] = v()
            else:
                d[k] = v
        return d

    def add_meta(self, key, val):
        """

        :param key:
        :param val:

        """
        self._meta[key] = val

    @property
    def name(self):
        """ """
        return self._name

    @property
    def _name_python_safe(self):
        """ """
        name = camel_to_snake(self._name)  # Camel to snake
        name = name.replace(" ", "_")  # Spaces to snake
        return name

    @property
    def _name_uri_safe(self):
        """ """
        return snake_to_spine(self._name_python_safe)

    def add_method(self, method: Callable, method_name: str):
        """

        :param method:
        :param method_name:

        """
        self.methods[method_name] = method

        if not hasattr(self, method_name):
            setattr(self, method_name, method)
        else:
            raise NameError(
                "Unable to bind method to extension. Method name already exists."
            )

    def static_file_url(self, filename: str):
        """

        :param filename: str:

        """
        static_repr = self.views.get("static")
        static_view = static_repr.get("view")
        static_endpoint = getattr(static_view, "endpoint", None)

        if not static_endpoint:
            return None

        return url_for(static_endpoint, path=filename, _external=True)


def find_instances_in_module(module, class_to_find):
    """Find instances of a particular class within a module

    :param module: Python module to search
    :param class_to_find: Python class to search for instances of
    :type class_to_find: class
    :returns: List of objects derived from `class_to_find`
    :rtype: list

    """
    objs = []
    for attribute in dir(module):
        if not attribute.startswith("__"):
            if isinstance(getattr(module, attribute), class_to_find):
                logging.debug("Found extension %s", getattr(module, attribute).name)
                objs.append(getattr(module, attribute))
    return objs


def find_extensions_in_file(extension_path: str, module_name="extensions") -> list:
    """Find LabThings extension objects from a particular Python file

    :param extension_path: Path to the extension file
    :type extension_path: str
    :param module_name: Name of the module to load extensions into.
            Defaults to "extensions".
    :type module_name: str
    :param extension_path: str:
    :returns: List of extension objects
    :rtype: list

    """
    logging.debug("Loading extensions from %s", extension_path)

    spec = util.spec_from_file_location(module_name, extension_path)
    mod = util.module_from_spec(spec)
    sys.modules[spec.name] = mod

    try:
        spec.loader.exec_module(mod)  # type: ignore
    except Exception:  # pylint: disable=broad-except
        logging.error(
            "Exception in extension path %s: \n%s",
            extension_path,
            traceback.format_exc(),
        )
        return []
    else:
        # TODO: Add documentation links to warnings
        if hasattr(mod, "LABTHINGS_EXTENSIONS"):
            ext_objects = []
            for ext_element in getattr(mod, "LABTHINGS_EXTENSIONS"):
                if inspect.isclass(ext_element) and issubclass(
                    ext_element, BaseExtension
                ):
                    ext_objects.append(ext_element())
                elif isinstance(ext_element, BaseExtension):
                    logging.warning(
                        "%s: Extension instance passed instead of class. LABTHINGS_EXTENSIONS should contain classes, not instances.",
                        ext_element,
                    )
                    ext_objects.append(ext_element)
                else:
                    logging.error(
                        "Unsupported extension type %s. Skipping.", type(ext_element)
                    )
            return ext_objects
        elif hasattr(mod, "__extensions__"):
            logging.warning(
                "Explicit extension list using the __extensions__ global is deprecated. Please use LABTHINGS_EXTENSIONS instead."
            )
            return [
                getattr(mod, ext_name) for ext_name in getattr(mod, "__extensions__")
            ]
        else:
            logging.warning(
                "No LTX_MANIFEST found for %s. Searching for implicit extension objects.",
                extension_path,
            )
            return find_instances_in_module(mod, BaseExtension)


def find_extensions(extension_dir: str, module_name="extensions") -> list:
    """Find LabThings extension objects from files in an extension directory

    :param extension_dir: Path to directory contatining extension files
    :type extension_dir: str
    :param module_name: Name of the module to load extensions into.
            Defaults to "extensions".
    :type module_name: str
    :param extension_dir: str:
    :returns: List of extension objects
    :rtype: list

    """
    logging.debug("Loading extensions from %s", extension_dir)

    extensions = []
    extension_paths = glob.glob(os.path.join(extension_dir, "*.py"))
    extension_paths.extend(glob.glob(os.path.join(extension_dir, "*", "__init__.py")))

    for extension_path in extension_paths:
        extensions.extend(
            find_extensions_in_file(extension_path, module_name=module_name)
        )

    return extensions
