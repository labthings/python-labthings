from flask import url_for, jsonify
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from . import EXTENSION_NAME  # TODO: Move into .names
from .names import TASK_ENDPOINT, TASK_LIST_ENDPOINT, EXTENSION_LIST_ENDPOINT
from .extensions import BaseExtension
from .utilities import description_from_view
from .spec.apispec import rule_to_apispec_path
from .spec.utilities import get_spec
from .spec.td import ThingDescription
from .decorators import tag

from .views.extensions import ExtensionList
from .views.tasks import TaskList, TaskView
from .views.docs import docs_blueprint, SwaggerUIView, W3CThingDescriptionView

from ..core.utilities import get_docstring

import logging


class LabThing(object):
    def __init__(
        self,
        app=None,
        prefix: str = "",
        title: str = "",
        description: str = "",
        version: str = "0.0.0",
    ):
        self.app = app

        self.components = {}

        self.extensions = {}

        self.views = []

        self.custom_root_links = {}

        self.endpoints = set()

        self.url_prefix = prefix
        self._description = description
        self._title = title
        self._version = version

        # Store handlers for things like errors and CORS
        self.handlers = {}

        self.spec = APISpec(
            title=self.title,
            version=self.version,
            openapi_version="3.0.2",
            plugins=[MarshmallowPlugin()],
        )

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
    def title(self,):
        return self._title

    @title.setter
    def title(self, title: str):
        self._title = title
        self.spec.title = title

    @property
    def version(self,):
        return str(self._version)

    @version.setter
    def version(self, version: str):
        self._version = version
        self.spec.version = version

    # Flask stuff

    def init_app(self, app):
        app.teardown_appcontext(self.teardown)

        # Register Flask extension
        app.extensions = getattr(app, "extensions", {})
        app.extensions[EXTENSION_NAME] = self

        # Add resources, if registered before tying to a Flask app
        if len(self.views) > 0:
            for resource, urls, endpoint, kwargs in self.views:
                self._register_view(app, resource, *urls, endpoint=endpoint, **kwargs)

        # Create base routes
        self._create_base_routes()

    def teardown(self, exception):
        pass

    def _create_base_routes(self):
        # Add root representation
        self.app.add_url_rule(self._complete_url("/", ""), "rootrep", self.rootrep)
        # Add thing descriptions
        self.app.register_blueprint(docs_blueprint, url_prefix=self.url_prefix)

        # Add extension overview
        self.add_view(ExtensionList, "/extensions", endpoint=EXTENSION_LIST_ENDPOINT)
        # Add task routes
        self.add_view(TaskList, "/tasks", endpoint=TASK_LIST_ENDPOINT)
        self.add_view(TaskView, "/tasks/<id>", endpoint=TASK_ENDPOINT)

    # Device stuff

    def add_component(self, device_object, device_name: str):
        self.components[device_name] = device_object

    # Extension stuff

    def register_extension(self, extension_object):
        if isinstance(extension_object, BaseExtension):
            self.extensions[extension_object.name] = extension_object
        else:
            raise TypeError("Extension object must be an instance of BaseExtension")

        for extension_view_id, extension_view in extension_object.views.items():
            # Add route to the extensions blueprint
            self.add_view(
                tag("extensions")(extension_view["view"]),
                "/extensions" + extension_view["rule"],
                **extension_view["kwargs"],
            )

    # Resource stuff

    def _complete_url(self, url_part, registration_prefix):
        """This method is used to defer the construction of the final url in
        the case that the Api is created with a Blueprint.
        :param url_part: The part of the url the endpoint is registered with
        :param registration_prefix: The part of the url contributed by the
            blueprint.  Generally speaking, BlueprintSetupState.url_prefix
        """
        parts = [registration_prefix, self.url_prefix, url_part]
        return "".join([part for part in parts if part])

    def add_view(self, resource, *urls, endpoint=None, **kwargs):
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
            api.add_resource(HelloWorld, '/', '/hello')
            api.add_resource(Foo, '/foo', endpoint="foo")
            api.add_resource(FooSpecial, '/special/foo', endpoint="foo")
        """
        endpoint = endpoint or resource.__name__.lower()

        logging.debug(f"{endpoint}: {type(resource)}")

        if self.app is not None:
            self._register_view(self.app, resource, *urls, endpoint=endpoint, **kwargs)

        self.views.append((resource, urls, endpoint, kwargs))

    def view(self, *urls, **kwargs):
        def decorator(cls):
            self.add_view(cls, *urls, **kwargs)
            return cls

        return decorator

    def _register_view(self, app, view, *urls, endpoint=None, **kwargs):
        endpoint = endpoint or view.__name__.lower()
        self.endpoints.add(endpoint)
        resource_class_args = kwargs.pop("resource_class_args", ())
        resource_class_kwargs = kwargs.pop("resource_class_kwargs", {})

        # NOTE: 'view_functions' is cleaned up from Blueprint class in Flask 1.0
        if endpoint in getattr(app, "view_functions", {}):
            previous_view_class = app.view_functions[endpoint].__dict__["view_class"]

            # If you override the endpoint with a different class,
            # avoid the collision by raising an exception
            if previous_view_class != view:
                raise ValueError(
                    "This endpoint (%s) is already set to the class %s."
                    % (endpoint, previous_view_class.__name__)
                )

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
        view_spec = get_spec(view)
        view_groups = view_spec.get("_groups", {})
        if "actions" in view_groups:
            self.thing_description.action(flask_rules, view)
        if "properties" in view_groups:
            self.thing_description.property(flask_rules, view)

    # Utilities

    def url_for(self, view, **values):
        """Generates a URL to the given resource.
        Works like :func:`flask.url_for`."""
        endpoint = view.endpoint
        return url_for(endpoint, **values)

    def owns_endpoint(self, endpoint):
        return endpoint in self.endpoints

    def add_root_link(self, view, title, kwargs=None):
        if kwargs is None:
            kwargs = {}
        self.custom_root_links[title] = (view, kwargs)

    # Description
    def rootrep(self):
        """
        Root representation
        """
        # TODO: Allow custom root representations

        rr = {
            "id": url_for("rootrep", _external=True),
            "title": self.title,
            "description": self.description,
            "links": {
                "thingDescription": {
                    "href": url_for("labthings_docs.w3c_td", _external=True),
                    "description": get_docstring(W3CThingDescriptionView),
                },
                "swaggerUI": {
                    "href": url_for("labthings_docs.swagger_ui", _external=True),
                    **description_from_view(SwaggerUIView),
                },
                "extensions": {
                    "href": self.url_for(ExtensionList, _external=True),
                    **description_from_view(ExtensionList),
                },
                "tasks": {
                    "href": self.url_for(TaskList, _external=True),
                    **description_from_view(TaskList),
                },
            },
        }

        for title, (view, kwargs) in self.custom_root_links.items():
            rr["links"][title] = {
                "href": self.url_for(view, **kwargs, _external=True),
                **description_from_view(view),
            }

        return jsonify(rr)
