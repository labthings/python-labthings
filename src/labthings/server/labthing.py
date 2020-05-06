from flask import url_for
from apispec import APISpec

# from apispec.ext.marshmallow import MarshmallowPlugin

from .names import (
    EXTENSION_NAME,
    TASK_ENDPOINT,
    TASK_LIST_ENDPOINT,
    EXTENSION_LIST_ENDPOINT,
)
from .extensions import BaseExtension
from .utilities import clean_url_string
from .exceptions import JSONExceptionHandler
from .logging import LabThingLogger
from .representations import LabThingsJSONEncoder
from .spec.apispec import rule_to_apispec_path
from .spec.apispec_plugins import MarshmallowPlugin
from .spec.utilities import get_spec
from .spec.td import ThingDescription
from .decorators import tag
from .sockets import Sockets
from .event import Event

from .view.builder import property_of, action_from

from .default_views.extensions import ExtensionList
from .default_views.tasks import TaskList, TaskView
from .default_views.docs import docs_blueprint, SwaggerUIView
from .default_views.root import RootView
from .default_views.sockets import socket_handler

from labthings.core.utilities import camel_to_snake

from typing import Callable

import weakref
import logging


class LabThing:
    def __init__(
        self,
        app=None,
        prefix: str = "",
        title: str = "",
        description: str = "",
        types: list = None,
        version: str = "0.0.0",
        format_flask_exceptions: bool = True,
    ):
        if types is None:
            types = []
        self.app = app  # Becomes a Flask app
        self.sockets = None  # Becomes a Socket(app) websocket handler

        self.components = {}

        self.extensions = {}

        self.events = {}

        self.views = []
        self._property_views = {}
        self._action_views = {}

        self.subscribers = set()

        self.endpoints = set()

        self.url_prefix = prefix

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

        # API Spec
        self.spec = APISpec(
            title=self.title,
            version=self.version,
            openapi_version="3.0.2",
            plugins=[MarshmallowPlugin()],
        )

        # Thing description
        self.thing_description = ThingDescription(self.spec)

        if app is not None:
            self.init_app(app)

    @property
    def description(self,):
        return self._description

    @description.setter
    def description(self, description: str):
        self._description = description
        self.spec.description = description

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title: str):
        self._title = title
        self.spec.title = title

    @property
    def safe_title(self):
        title = self.title
        if not title:
            title = "unknown"
        title = title.replace(" ", "")
        title = title.lower()
        return title

    @property
    def version(self,):
        return str(self._version)

    @version.setter
    def version(self, version: str):
        self._version = version
        self.spec.version = version

    # Flask stuff

    def init_app(self, app):
        self.app = app

        # Register Flask extension
        app.extensions = getattr(app, "extensions", {})
        app.extensions[EXTENSION_NAME] = weakref.ref(self)

        # Flask error formatter
        if self.format_flask_exceptions:
            error_handler = JSONExceptionHandler()
            error_handler.init_app(app)

        # Custom JSON encoder
        app.json_encoder = LabThingsJSONEncoder

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
        self.add_root_link(TaskList, "tasks")
        self.add_view(TaskView, "/tasks/<task_id>", endpoint=TASK_ENDPOINT)

    def _create_base_sockets(self):
        self.sockets.add_view(
            self._complete_url("/ws", ""), socket_handler, endpoint="ws"
        )
        self.thing_description.add_link("ws", "websocket")

    # Device stuff

    def add_component(self, device_object, device_name: str):
        self.components[device_name] = device_object

        for extension_object in self.extensions.values():
            # For each on_component function
            for com_func in extension_object._on_components:
                # If the component matches
                if com_func.get("component", "") == device_name:
                    # Call the function
                    com_func.get("function")(
                        device_object, *com_func.get("args"), **com_func.get("kwargs")
                    )

    # Extension stuff

    def register_extension(self, extension_object):
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
                tag("extensions")(extension_view["view"]),
                "/extensions" + extension_view["rule"],
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
        :param resource: the class name of your resource
        :type resource: :class:`Type[Resource]`
        :param urls: one or more url routes to match for the resource, standard
                    flask routing rules apply.  Any url variables will be
                    passed to the resource method as args.
        :type urls: str
        :param endpoint: endpoint name (defaults to :meth:`Resource.__name__`
            Can be used to reference this route in :class:`fields.Url` fields
        :type endpoint: str
        :param resource_class_args: args to be forwarded to the constructor of
            the resource.
        :type resource_class_args: tuple
        :param resource_class_kwargs: kwargs to be forwarded to the constructor
            of the resource.
        :type resource_class_kwargs: dict
        Additional keyword arguments not specified above will be passed as-is
        to :meth:`flask.Flask.add_url_rule`.
        Examples::
            api.add_view(HelloWorld, '/', '/hello')
            api.add_view(Foo, '/foo', endpoint="foo")
            api.add_view(FooSpecial, '/special/foo', endpoint="foo")
        """
        endpoint = endpoint or camel_to_snake(view.__name__)

        logging.debug(f"{endpoint}: {type(view)} @ {urls}")

        if self.app is not None:
            self._register_view(self.app, view, *urls, endpoint=endpoint, **kwargs)

        self.views.append((view, urls, endpoint, kwargs))

    def view(self, *urls, **kwargs):
        def decorator(cls):
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
        # FIXME: There is a MASSIVE memory leak or something going on in APISpec!
        # This is grinding tests to a halt, and is really annoying... Should be fixed.
        flask_rules = app.url_map._rules_by_endpoint.get(endpoint)  # skipcq: PYL-W0212
        for flask_rule in flask_rules:
            self.spec.path(**rule_to_apispec_path(flask_rule, view, self.spec))

        # Handle resource groups listed in API spec
        view_spec = get_spec(view)
        view_tags = view_spec.get("tags", set())
        if "actions" in view_tags:
            self.thing_description.action(flask_rules, view)
            # TODO: Use this for top-level action POST
            self._action_views[view.endpoint] = view
        if "properties" in view_tags:
            self.thing_description.property(flask_rules, view)
            self._property_views[view.endpoint] = view

    # Event stuff
    def add_event(self, name, schema=None):
        # TODO: Handle schema
        # TODO: Add view for event, returning list of Event.events
        self.events[name] = Event(name, schema=schema)
        self.thing_description.event(self.events[name])

    def emit(self, event_type: str, data: dict):
        """
        Find a matching event type if one exists, and emit some data to it
        """
        event_object = self.events[event_type]
        self.message(event_object, data)

    def message(self, event: Event, data: dict):
        """
        Emit an event object to all subscribers
        """
        event_response = event.emit(data)
        for sub in self.subscribers:
            sub.emit(event_response)

    # Utilities

    def url_for(self, view, **values):
        """Generates a URL to the given resource.
        Works like :func:`flask.url_for`."""
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

    def owns_endpoint(self, endpoint):
        return endpoint in self.endpoints

    def add_root_link(self, view, rel, kwargs=None, params=None):
        if kwargs is None:
            kwargs = {}
        if params is None:
            params = {}
        self.thing_description.add_link(view, rel, kwargs=kwargs, params=params)

    # Convenience methods
    def build_property(
        self, property_object: object, property_name: str, *urls, **kwargs
    ):
        self.add_view(property_of(property_object, property_name, **kwargs), *urls)

    def build_action(self, function: Callable, *urls, **kwargs):
        self.add_view(action_from(function, **kwargs), *urls)
