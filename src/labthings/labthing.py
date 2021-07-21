import logging
import uuid
import weakref
from json import JSONEncoder
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type

from apispec import APISpec
from apispec_webframeworks.flask import FlaskPlugin
from flask import Flask, url_for

from .actions.pool import Pool
from .apispec import FlaskLabThingsPlugin, MarshmallowPlugin
from .default_views.actions import ActionObjectView, ActionQueueView
from .default_views.docs import SwaggerUIView, docs_blueprint
from .default_views.events import LoggingEventView
from .default_views.extensions import ExtensionList
from .default_views.root import RootView
from .extensions import BaseExtension
from .httperrorhandler import SerializedExceptionHandler
from .json.encoder import LabThingsJSONEncoder
from .logging import LabThingLogger
from .names import (
    ACTION_ENDPOINT,
    ACTION_LIST_ENDPOINT,
    EXTENSION_LIST_ENDPOINT,
    EXTENSION_NAME,
    LOG_EVENT_ENDPOINT,
)
from .representations import DEFAULT_REPRESENTATIONS
from .td import ThingDescription
from .utilities import clean_url_string, snake_to_camel
from .views import ActionView, EventView, PropertyView, View

# from apispec.ext.marshmallow import MarshmallowPlugin


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
    :param external_links: Use external links in Thing Description where possible
    :type external_links: bool
    :param json_encoder: JSON encoder class for the app
    """

    def __init__(
        self,
        app: Optional[Flask] = None,
        id_: str = None,
        prefix: str = "",
        title: str = "",
        description: str = "",
        version: str = "0.0.0",
        types: Optional[List[str]] = None,
        format_flask_exceptions: bool = True,
        external_links: bool = True,
        json_encoder=LabThingsJSONEncoder,
    ):
        if id_ is None:
            self.id = f"{title}:{uuid.uuid4()}".replace(" ", "")
        else:
            self.id = id_

        self.app: Optional[Flask] = app  # Becomes a Flask app

        self.components: Dict[
            str, Any
        ] = {}  # Dictionary of attached component objects, available to extensions

        self.extensions: Dict[
            str, BaseExtension
        ] = {}  # Dictionary of LabThings extension objects

        self.actions = Pool()  # Pool of threads for Actions

        self.views: List[Tuple] = []  # List of View classes
        self._property_views: Dict[
            str, Type[PropertyView]
        ] = {}  # Dictionary of PropertyView views
        self._action_views: Dict[
            str, Type[ActionView]
        ] = {}  # Dictionary of ActionView views
        self._event_views: Dict[
            str, Type[EventView]
        ] = {}  # Dictionary of EventView views

        self.endpoints: Set[str] = set()  # Set of endpoint strings

        self.url_prefix = prefix  # Global URL prefix for all LabThings views

        self.types: List[str] = types or []

        self._description: str = description
        self._title: str = title
        self._version: str = version

        # Flags for error handling
        self.format_flask_exceptions: bool = format_flask_exceptions

        # Logging handler
        self.log_handler: LabThingLogger = LabThingLogger(self)
        logging.getLogger().addHandler(self.log_handler)

        # Representation formatter map
        self.representations: Dict[str, Callable] = DEFAULT_REPRESENTATIONS

        # OpenAPI spec for Swagger docs
        self.spec: APISpec = APISpec(
            title=self.title,
            version=self.version,
            openapi_version="3.0.2",
            plugins=[FlaskPlugin(), FlaskLabThingsPlugin(), MarshmallowPlugin()],
        )

        # Thing description
        self.thing_description: ThingDescription = ThingDescription(
            external_links=external_links
        )

        # JSON encoder class
        self.json_encoder: JSONEncoder = json_encoder

        if app is not None:
            self.init_app(app)

    @property
    def description(
        self,
    ) -> str:
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
    def title(self) -> str:
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
    def safe_title(self) -> str:
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
    def version(self) -> str:
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
        # Add action routes
        self.add_view(ActionQueueView, "/actions", endpoint=ACTION_LIST_ENDPOINT)
        self.add_root_link(ActionQueueView, "actions")
        self.add_view(ActionObjectView, "/actions/<task_id>", endpoint=ACTION_ENDPOINT)
        # Add event routes
        self.add_view(LoggingEventView, "/events/logging", endpoint=LOG_EVENT_ENDPOINT)

    # Device stuff

    def add_component(self, component_object, component_name: str):
        """
        Add a component object to the LabThing, allowing it to be
        used by extensions and other views by name, rather than reference.

        :param device_object: Component object
        :param device_name: str: Component name, used by extensions to find the object

        """
        self.components[component_name] = component_object

        def dummy(*_):
            pass

        for extension_object in self.extensions.values():
            # For each on_component function
            for com_func in extension_object.on_components:
                # If the component matches
                if com_func.get("component", "") == component_name:
                    # Call the function
                    com_func.get("function", dummy)(
                        component_object,
                        *com_func.get("args"),
                        **com_func.get("kwargs"),
                    )

    # Extension stuff

    def register_extension(self, extension_object: BaseExtension):
        """
        Add an extension to the LabThing. This will add API views and lifecycle
        functions from the extension to the LabThing

        :param extension_object: Extension instance
        :type extension_object: labthings.extensions.BaseExtension

        """

        def dummy(*_):
            pass

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
        for reg_func in extension_object.on_registers:
            # Call the function
            reg_func.get("function", dummy)(
                *reg_func.get("args"), **reg_func.get("kwargs")
            )

        # For each on_component function
        for com_func in extension_object.on_components:
            key = com_func.get("component", "")
            # If the component has already been added
            if key in self.components:
                # Call the function
                com_func.get("function", dummy)(
                    self.components.get(key),
                    *com_func.get("args"),
                    **com_func.get("kwargs"),
                )

    # Resource stuff

    def _complete_url(self, url_part: str, registration_prefix: str) -> str:
        """This method is used to defer the construction of the final url in
        the case that the Api is created with a Blueprint.

        :param url_part: The part of the url the endpoint is registered with
        :param registration_prefix: The part of the url contributed by the
            blueprint.  Generally speaking, BlueprintSetupState.url_prefix

        """
        parts = [self.url_prefix, registration_prefix, url_part]
        u = "".join(clean_url_string(part) for part in parts if part)
        return u if u else "/"

    def add_view(
        self, view: Type[View], *urls: str, endpoint: Optional[str] = None, **kwargs
    ):
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
        endpoint = endpoint or snake_to_camel(view.__name__)

        logging.debug("%s: %s @ %s", endpoint, type(view), urls)

        if self.app is not None:
            self._register_view(self.app, view, *urls, endpoint=endpoint, **kwargs)

        self.views.append((view, urls, endpoint, kwargs))

    def view(self, *urls: str, **kwargs):
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

    def _register_view(
        self,
        app,
        view: Type[View],
        *urls: str,
        endpoint: Optional[str] = None,
        **kwargs,
    ):
        endpoint = endpoint or view.__name__
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
            app.add_url_rule(rule, view_func=resource_func, endpoint=endpoint, **kwargs)

        # There might be a better way to do this than _rules_by_endpoint,
        # but I can't find one so this will do for now.
        # pylint: disable=protected-access
        flask_rules = app.url_map._rules_by_endpoint.get(endpoint)
        with app.test_request_context():
            self.spec.path(view=resource_func, interaction=view)

        # Handle resource groups listed in API spec
        if issubclass(view, ActionView):
            self.thing_description.action(flask_rules, view)
            self._action_views[view.endpoint] = view
        if issubclass(view, PropertyView):
            self.thing_description.property(flask_rules, view)
            self._property_views[view.endpoint] = view
        if issubclass(view, EventView):
            self.thing_description.event(flask_rules, view)
            self._event_views[view.endpoint] = view

    def emit(self, event_type: str, data: dict):
        """Find a matching event type if one exists, and emit some data to it

        :param event_type: str:
        :param data: dict:

        """
        event_view = self._event_views.get(event_type)
        if event_view:
            event_view.emit(data)

    # Utilities

    def url_for(self, view: Type[View], **values):
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

    def add_root_link(self, view: Type[View], rel: str, kwargs=None, params=None):
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
