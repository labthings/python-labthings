from flask import url_for
from flask_threaded_sockets import Sockets
from apispec import APISpec

# from apispec.ext.marshmallow import MarshmallowPlugin

from .names import (
    EXTENSION_NAME,
    TASK_ENDPOINT,
    TASK_LIST_ENDPOINT,
    ACTION_ENDPOINT,
    ACTION_LIST_ENDPOINT,
    EXTENSION_LIST_ENDPOINT,
)
from .extensions import BaseExtension
from .utilities import clean_url_string
from .httperrorhandler import SerializedExceptionHandler
from .logging import LabThingLogger
from .json.encoder import LabThingsJSONEncoder
from .representations import DEFAULT_REPRESENTATIONS
from .apispec import MarshmallowPlugin, rule_to_apispec_path
from .td import ThingDescription
from .event import Event

from .actions.pool import Pool

from .views.builder import property_of, action_from

from .default_views.extensions import ExtensionList
from .default_views.tasks import TaskList, TaskView
from .default_views.actions import ActionQueue, ActionView
from .default_views.docs import docs_blueprint, SwaggerUIView
from .default_views.root import RootView
from .default_views.sockets import socket_handler

from .utilities import camel_to_snake, url_for_property, url_for_action

from typing import Callable

import weakref
import logging


class LabThing:
    """
    The main entry point for the application.
    You need to initialize it with a Flask Application: ::

    >>> app = Flask(__name__)
    >>> labthing = labthings.LabThing(app)

    Alternatively, you can use :meth:`init_app` to set the Flask application
    after it has been constructed.

    :param app: the Flask application object
    :type app: flask.Flask
    :param prefix: Prefix all routes with a value, eg v1 or 2010-04-01
    :type prefix: str
    :param title: Human-readable title of the Thing
    :type title: str
    :param description: Human-readable description of the Thing
    :type description: str
    :param version: Version number of the Thing
    :type version: str
    :param types: List of Thing types, used by clients to filter discovered Things
    :type types: list of str
    :param format_flask_exceptions: JSON format all exception responses
    :type format_flask_exceptions: bool
    :param json_encoder: JSON encoder class for the app
    """

    def __init__(
        self,
        app=None,
        prefix: str = "",
        title: str = "",
        description: str = "",
        version: str = "0.0.0",
        types: list = None,
        format_flask_exceptions: bool = True,
        json_encoder=LabThingsJSONEncoder,
    ):
        if types is None:
            types = []
        self.app = app  # Becomes a Flask app
        self.sockets = None  # Becomes a Socket(app) websocket handler

        self.components = (
            {}
        )  # Dictionary of attached component objects, available to extensions

        self.extensions = {}  # Dictionary of LabThings extension objects

        self.actions = Pool()  # Pool of threads for Actions

        self.events = {}  # Dictionary of Event affordances

        self.views = []  # List of View classes
        self._property_views = {}  # Dictionary of PropertyView views
        self._action_views = {}  # Dictionary of ActionView views

        self.subscribers = set()  # Set of connected event subscribers

        self.endpoints = set()  # Set of endpoint strings

        self.url_prefix = prefix  # Global URL prefix for all LabThings views

        for t in types:
            if ";" in t:
                raise ValueError(
                    f'Error in type value "{t}". Thing types cannot contain ; character.'
                )
        self.types = types

        self._description = description
        self._title = title
        self._version = version

        # Flags for error handling
        self.format_flask_exceptions = format_flask_exceptions

        # Logging handler
        # TODO: Add cleanup code
        self.log_handler = LabThingLogger()
        logging.getLogger().addHandler(self.log_handler)

        # Representation formatter map
        self.representations = DEFAULT_REPRESENTATIONS

        # OpenAPI spec for Swagger docs
        self.spec = APISpec(
            title=self.title,
            version=self.version,
            openapi_version="3.0.2",
            plugins=[MarshmallowPlugin()],
        )

        # Thing description
        self.thing_description = ThingDescription()

        # JSON encoder class
        self.json_encoder = json_encoder

        if app is not None:
            self.init_app(app)

    @property
    def description(self,):
        """
        Human-readable description of the Thing
        """
        return self._description

    @description.setter
    def description(self, description: str):
        """
        Human-readable description of the Thing
        :param description: str: 
        """
        self._description = description
        self.spec.description = description

    @property
    def title(self):
        """
        Human-readable title of the Thing
        """
        return self._title

    @title.setter
    def title(self, title: str):
        """
        Human-readable title of the Thing
        :param description: str: 
        """
        self._title = title
        self.spec.title = title

    @property
    def safe_title(self):
        """
        Lowercase title with no whitespace
        """
        title = self.title
        if not title:
            title = "unknown"
        title = title.replace(" ", "")
        title = title.lower()
        return title

    @property
    def version(self,):
        """
        Version number of the Thing
        """
        return str(self._version)

    @version.setter
    def version(self, version: str):
        """
        Version number of the Thing
        :param version: str: 
        """
        self._version = version
        self.spec.version = version

    # Flask stuff

    def init_app(self, app):
        """
        Initialize this class with the given :class:`flask.Flask` application.
        :param app: the Flask application or blueprint object

        :type app: flask.Flask
        :type app: flask.Blueprint

        Examples::
            labthing = LabThing()
            labthing.add_view(...)
            labthing.init_app(app)
        """
        self.app = app

        # Register Flask extension
        app.extensions = getattr(app, "extensions", {})
        app.extensions[EXTENSION_NAME] = weakref.ref(self)

        # Flask error formatter
        if self.format_flask_exceptions:
            error_handler = SerializedExceptionHandler()
            error_handler.init_app(app)

        # Custom JSON encoder
        app.json_encoder = self.json_encoder

        # Add resources, if registered before tying to a Flask app
        if len(self.views) > 0:
            for resource, urls, endpoint, kwargs in self.views:
                self._register_view(app, resource, *urls, endpoint=endpoint, **kwargs)

        # Create base routes
        self._create_base_routes()

        # Create socket handler
        self.sockets = Sockets(app)
        self._create_base_sockets()

        # Create base events
        self.add_event("logging")

    def _create_base_routes(self):
        """
        Automatically add base HTTP views to the LabThing.

        Creates:
            Root Thing Description
            Extensions list
            Legacy task list and resources
            Actions queue and resources
        """
        # Add root representation
        self.add_view(RootView, "/", endpoint="root")
        # Add thing descriptions
        self.app.register_blueprint(
            docs_blueprint, url_prefix=f"{self.url_prefix}/docs"
        )
        self.add_root_link(SwaggerUIView, "docs")

        # Add extension overview
        self.add_view(ExtensionList, "/extensions", endpoint=EXTENSION_LIST_ENDPOINT)
        self.add_root_link(ExtensionList, "extensions")
        # Add task routes
        self.add_view(TaskList, "/tasks", endpoint=TASK_LIST_ENDPOINT)
        self.add_view(TaskView, "/tasks/<task_id>", endpoint=TASK_ENDPOINT)
        # Add action routes
        self.add_view(ActionQueue, "/actions", endpoint=ACTION_LIST_ENDPOINT)
        self.add_root_link(ActionQueue, "actions")
        self.add_view(ActionView, "/actions/<task_id>", endpoint=ACTION_ENDPOINT)

    def _create_base_sockets(self):
        """
        Automatically add base WebSocket views to the LabThing.
        """
        self.sockets.add_view(
            self._complete_url("/ws", ""), socket_handler, endpoint="ws"
        )
        self.thing_description.add_link("ws", "websocket")

    # Device stuff

    def add_component(self, component_object, component_name: str):
        """
        Add a component object to the LabThing, allowing it to be
        used by extensions and other views by name, rather than reference.

        :param device_object: Component object
        :param device_name: str: Component name, used by extensions to find the object

        """
        self.components[component_name] = component_object

        for extension_object in self.extensions.values():
            # For each on_component function
            for com_func in extension_object._on_components:
                # If the component matches
                if com_func.get("component", "") == component_name:
                    # Call the function
                    com_func.get("function")(
                        component_object,
                        *com_func.get("args"),
                        **com_func.get("kwargs"),
                    )

    # Extension stuff

    def register_extension(self, extension_object):
        """
        Add an extension to the LabThing. This will add API views and lifecycle 
        functions from the extension to the LabThing

        :param extension_object: Extension instance
        :type extension_object: labthings.extensions.BaseExtension

        """
        # Type check
        if isinstance(extension_object, BaseExtension):
            self.extensions[extension_object.name] = extension_object
        else:
            raise TypeError("Extension object must be an instance of BaseExtension")

        for extension_view_endpoint, extension_view in extension_object.views.items():

            # Append extension name to endpoint
            endpoint = f"{extension_object.name}/{extension_view_endpoint}"

            # Add route to the extensions blueprint
            self.add_view(
                extension_view["view"],
                *("/extensions" + url for url in extension_view["urls"]),
                endpoint=endpoint,
                **extension_view["kwargs"],
            )

        # For each on_register function
        for reg_func in extension_object._on_registers:
            # Call the function
            reg_func.get("function")(*reg_func.get("args"), **reg_func.get("kwargs"))

        # For each on_component function
        for com_func in extension_object._on_components:
            key = com_func.get("component", "")
            # If the component has already been added
            if key in self.components:
                # Call the function
                com_func.get("function")(
                    self.components.get(key),
                    *com_func.get("args"),
                    **com_func.get("kwargs"),
                )

    # Resource stuff

    def _complete_url(self, url_part, registration_prefix):
        """This method is used to defer the construction of the final url in
        the case that the Api is created with a Blueprint.

        :param url_part: The part of the url the endpoint is registered with
        :param registration_prefix: The part of the url contributed by the
            blueprint.  Generally speaking, BlueprintSetupState.url_prefix

        """
        parts = [self.url_prefix, registration_prefix, url_part]
        u = "".join(clean_url_string(part) for part in parts if part)
        return u if u else "/"

    def add_view(self, view, *urls, endpoint=None, **kwargs):
        """Adds a view to the api.

        :param view: View class
        :type resource: :class:`labthings.views.View`
        :param urls: one or more url routes to match for the resource, standard
                    flask routing rules apply.  Any url variables will be
                    passed to the resource method as args.
        :type urls: str
        :param endpoint: endpoint name (defaults to :meth:`Resource.__name__`
            Can be used to reference this route in :class:`fields.Url` fields
        :type endpoint: str
        :param kwargs: kwargs to be forwarded to the constructor
            of the view.

        Additional keyword arguments not specified above will be passed as-is
        to :meth:`flask.Flask.add_url_rule`.

        Examples::

            labthing.add_view(HelloWorld, '/', '/hello')
            labthing.add_view(Foo, '/foo', endpoint="foo")
            labthing.add_view(FooSpecial, '/special/foo', endpoint="foo")
        """
        endpoint = endpoint or camel_to_snake(view.__name__)

        logging.debug(f"{endpoint}: {type(view)} @ {urls}")

        if self.app is not None:
            self._register_view(self.app, view, *urls, endpoint=endpoint, **kwargs)

        self.views.append((view, urls, endpoint, kwargs))

    def view(self, *urls, **kwargs):
        """Wraps a :class:`labthings.View` class, adding it to the LabThing. 
        Parameters are the same as :meth:`~labthings.LabThing.add_view`.

        Example::

            app = Flask(__name__)
            labthing = labthings.LabThing(app)

            @labthing.view('/properties/my_property')
            class Foo(labthings.views.PropertyView):
                schema = labthings.fields.String()

                def get(self):
                    return 'Hello, World!'
        """

        def decorator(cls):
            """ """
            self.add_view(cls, *urls, **kwargs)
            return cls

        return decorator

    def _register_view(self, app, view, *urls, endpoint=None, **kwargs):
        endpoint = endpoint or camel_to_snake(view.__name__)
        self.endpoints.add(endpoint)
        resource_class_args = kwargs.pop("resource_class_args", ())
        resource_class_kwargs = kwargs.pop("resource_class_kwargs", {})

        view.endpoint = endpoint
        resource_func = view.as_view(
            endpoint, *resource_class_args, **resource_class_kwargs
        )

        for url in urls:
            # If we've got no Blueprint, just build a url with no prefix
            rule = self._complete_url(url, "")
            # Add the url to the application or blueprint
            app.add_url_rule(rule, view_func=resource_func, **kwargs)

        # There might be a better way to do this than _rules_by_endpoint,
        # but I can't find one so this will do for now. Skipping PYL-W0212
        flask_rules = app.url_map._rules_by_endpoint.get(endpoint)  # skipcq: PYL-W0212
        for flask_rule in flask_rules:
            self.spec.path(**rule_to_apispec_path(flask_rule, view, self.spec))

        # Handle resource groups listed in API spec
        if hasattr(view, "get_tags"):
            if "actions" in view.get_tags():
                self.thing_description.action(flask_rules, view)
                self._action_views[view.endpoint] = view
            if "properties" in view.get_tags():
                self.thing_description.property(flask_rules, view)
                self._property_views[view.endpoint] = view

    # Event stuff
    def add_event(self, name, schema=None):
        """

        :param name: 
        :param schema:  (Default value = None)

        """
        # TODO: Handle schema
        # TODO: Add view for event, returning list of Event.events
        self.events[name] = Event(name, schema=schema)
        self.thing_description.event(self.events[name])

    def emit(self, event_type: str, data: dict):
        """Find a matching event type if one exists, and emit some data to it

        :param event_type: str: 
        :param data: dict: 

        """
        event_object = self.events[event_type]
        self.message(event_object, data)

    def message(self, event: Event, data: dict):
        """Emit an event object to all subscribers

        :param event: Event: 
        :param data: dict: 

        """
        event_response = event.emit(data)
        for sub in self.subscribers:
            sub.emit(event_response)

    # Utilities

    def url_for(self, view, **values):
        """Generates a URL to the given resource.
        Works like :func:`flask.url_for`.

        :param view: 
        :param values: 

        """
        if isinstance(view, str):
            endpoint = view
        else:
            endpoint = getattr(view, "endpoint", None)
        if not endpoint:
            return ""
        # Default to external links
        if "_external" not in values:
            values["_external"] = True
        return url_for(endpoint, **values)

    def add_root_link(self, view, rel, kwargs=None, params=None):
        """

        :param view: 
        :param rel: 
        :param kwargs:  (Default value = None)
        :param params:  (Default value = None)

        """
        if kwargs is None:
            kwargs = {}
        if params is None:
            params = {}
        self.thing_description.add_link(view, rel, kwargs=kwargs, params=params)

    # Convenience methods
    def build_property(
        self, property_object: object, property_name: str, urls: list = None, **kwargs
    ):
        """
        Build an API Property from a Python object property, and add it to the API.

        :param property_object: object: Python object containing the property
        :param property_name: str: Name of the property on the Python object
        :param urls: list:  (Default value = None)  Custom URLs for the Property. If None, the URL will be automatically generated.
        :param readonly:  (Default value = False) Is the property read-only?
        :param description:  (Default value = None) Human readable description of the property
        :param schema:  (Default value = fields.Field()) Marshmallow schema for the property
        :type schema: :class:`labthings.fields.Field` or :class:`labthings.schema.Schema`
        :param semtype:  (Default value = None) Optional semantic object containing schema and annotations
        :type semtype: :class:`labthings.semantics.Semantic`
        """
        if urls is None:
            urls = [url_for_property(property_object, property_name)]
        self.add_view(property_of(property_object, property_name, **kwargs), *urls)

    def build_action(
        self, action_object: object, action_name: str, urls: list = None, **kwargs
    ):
        """
        Build an API Action from a Python object method, and add it to the API.

        :param action_object: object: Python object containing the action method
        :param action_name: str: Name of the method on the Python object
        :param urls: list:  (Default value = None)  Custom URLs for the Property. If None, the URL will be automatically generated.
        :param safe:  (Default value = False) Is the action safe
        :param idempotent:  (Default value = False) Is the action idempotent
        :param description:  (Default value = None) Human readable description of the property
        :param args:  (Default value = fields.Field()) Marshmallow schema for the method arguments
        :type args: :class:`labthings.schema.Schema`
        :param schema:  (Default value = fields.Field()) Marshmallow schema for the method response
        :type schema: :class:`labthings.fields.Field` or :class:`labthings.schema.Schema`
        :param semtype:  (Default value = None) Optional semantic object containing schema and annotations
        :type semtype: :class:`labthings.semantics.Semantic`

        """
        if urls is None:
            urls = [url_for_action(action_object, action_name)]
        self.add_view(action_from(action_object, action_name, **kwargs), *urls)
