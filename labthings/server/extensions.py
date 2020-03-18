import logging
import traceback

from importlib import util
import sys
import os
import glob

from .view.builder import static_from
from ..core.utilities import get_docstring, camel_to_snake, snake_to_spine


class BaseExtension:
    """
    Parent class for all extensions.

    Handles binding route views and forms.
    """

    # TODO: Allow adding components to extensions

    def __init__(
        self,
        name: str,
        description="",
        version="0.0.0",
        static_url_path="/static",
        static_folder=None,
    ):
        self._views = (
            {}
        )  # Key: Full, Python-safe ID. Val: Original rule, and view class
        self._rules = {}  # Key: Original rule. Val: View class
        self._meta = {}  # Extra metadata to add to the extension description

        self._on_registers = (
            []
        )  # List of dictionaries of functions to run on registration

        self._on_components = (
            []
        )  # List of dictionaries of functions to run as components are added

        self._cls = str(self)  # String description of extension instance

        self.actions = []
        self.properties = []

        self._name = name
        self.description = description or get_docstring(self)
        self.version = str(version)

        self.methods = {}

        if static_folder:
            print(f"Adding route for {static_folder}")
            self.static_view_class = static_from(static_folder)
            self.add_view(self.static_view_class, f"{static_url_path}/<path:path>")
        else:
            self.static_view_class = None

    @property
    def views(self):
        return self._views

    def add_view(self, view_class, rule, **kwargs):
        # Remove all leading slashes from view route
        cleaned_rule = rule
        while cleaned_rule[0] == "/":
            cleaned_rule = cleaned_rule[1:]

        # Expand the rule to include extension name
        full_rule = "/{}/{}".format(self._name_uri_safe, cleaned_rule)

        view_id = (
            cleaned_rule.replace("/", "_")
            .replace("<", "")
            .replace(">", "")
            .replace(":", "_")
        )

        # Store route information in a dictionary
        d = {"rule": full_rule, "view": view_class, "kwargs": kwargs}

        # Add view to private views dictionary
        self._views[view_id] = d
        # Store the rule expansion information
        self._rules[rule] = self._views[view_id]

    def on_register(self, function, args=None, kwargs=None):
        if not callable(function):
            raise TypeError("Function must be a callable")

        self._on_registers.append(
            {"function": function, "args": args or (), "kwargs": kwargs or {}}
        )

    def on_component(self, component_name: str, function, args=None, kwargs=None):
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
        d = {}
        for k, v in self._meta.items():
            if callable(v):
                d[k] = v()
            else:
                d[k] = v
        return d

    def add_meta(self, key, val):
        self._meta[key] = val

    @property
    def name(self):
        return self._name

    @property
    def _name_python_safe(self):
        name = camel_to_snake(self._name)  # Camel to snake
        name = name.replace(" ", "_")  # Spaces to snake
        return name

    @property
    def _name_uri_safe(self):
        return snake_to_spine(self._name_python_safe)

    def add_method(self, method, method_name):
        self.methods[method_name] = method

        if not hasattr(self, method_name):
            setattr(self, method_name, method)
        else:
            logging.warning(
                "Unable to bind method to extension. Method name already exists."
            )


def find_instances_in_module(module, class_to_find):
    """Find instances of a particular class within a module
    
    Args:
        module: Python module to search
        class_to_find (class): Python class to search for instances of
    
    Returns:
        list: List of objects derived from `class_to_find`
    """
    objs = []
    for attribute in dir(module):
        if not attribute.startswith("__"):
            if isinstance(getattr(module, attribute), class_to_find):
                logging.debug(f"Found extension {getattr(module, attribute).name}")
                objs.append(getattr(module, attribute))
    return objs


def find_extensions_in_file(extension_path: str, module_name="extensions") -> list:
    """Find LabThings extension objects from a particular Python file
    
    Args:
        extension_path (str): Path to the extension file
        module_name (str, optional): Name of the module to load extensions into.
            Defaults to "extensions".
    
    Returns:
        list: List of extension objects
    """
    logging.debug(f"Loading extensions from {extension_path}")

    spec = util.spec_from_file_location(module_name, extension_path)
    mod = util.module_from_spec(spec)
    sys.modules[spec.name] = mod

    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # skipcq: PYL-W0703
        logging.error(
            f"Exception in extension path {extension_path}: \n{traceback.format_exc()}"
        )
        return []
    else:
        if hasattr(mod, "__extensions__"):
            return [getattr(mod, ext_name) for ext_name in mod.__extensions__]
        else:
            return find_instances_in_module(mod, BaseExtension)


def find_extensions(extension_dir: str, module_name="extensions") -> list:
    """Find LabThings extension objects from files in an extension directory
    
    Args:
        extension_dir (str): Path to directory contatining extension files
        module_name (str, optional): Name of the module to load extensions into.
            Defaults to "extensions".
    
    Returns:
        list: List of extension objects
    """
    logging.debug(f"Loading extensions from {extension_dir}")

    extensions = []
    extension_paths = glob.glob(os.path.join(extension_dir, "*.py"))

    for extension_path in extension_paths:
        extensions.extend(
            find_extensions_in_file(extension_path, module_name=module_name)
        )

    return extensions
