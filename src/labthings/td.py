from typing import Any, Dict, List, Type

from flask import has_request_context, request

from .find import current_labthing
from .json.schemas import rule_to_params, rule_to_path, schema_to_json
from .schema import build_action_schema
from .utilities import ResourceURL, get_docstring
from .views import ActionView, EventView, PropertyView, View


def view_to_thing_forms(
    rules: list, view: Type[View], external: bool = True
) -> List[dict]:
    """Build a W3C form description for an general View

    :param rules: List of Flask rules
    :type rules: list
    :param view: View class
    :type view: View
    :param rules: list:
    :param view: View:
    :param external: bool: Use external links where possible
    :returns: Form description
    :rtype: [dict]

    """
    forms = []

    # Get map from ops to HTTP methods
    for op, meth in getattr(view, "_opmap", {}).items():
        if hasattr(view, meth):
            prop_urls = [rule_to_path(rule) for rule in rules]

            # Get content_types
            content_type = getattr(view, "content_type", "application/json")
            response_content_type = getattr(
                view, "response_content_type", "application/json"
            )

            for url in prop_urls:
                # Basic form parameters
                form = {
                    "op": op,
                    "href": ResourceURL(url, external=external),
                    "contentType": content_type,
                }
                # Optional override response content type
                if response_content_type != content_type:
                    form["response"] = {"contentType": response_content_type}
                # Add HTTP methods
                else:
                    form["htv:methodName"] = meth.upper()
                    form["href"] = ResourceURL(url, external=external)

                forms.append(form)

    return forms


class ThingDescription:
    """ """

    def __init__(self, external_links: bool = True):
        # Public attributes
        self.properties: Dict[str, dict] = {}
        self.actions: Dict[str, dict] = {}
        self.events: Dict[str, dict] = {}

        # Private attributes
        self._links: List[dict] = []

        # Settings
        self.external_links: bool = external_links

        # Init
        super().__init__()

    @property
    def links(self) -> List[Dict]:
        """ """
        td_links = []
        for link_description in self._links:
            td_links.append(
                {
                    "rel": link_description.get("rel"),
                    "href": current_labthing().url_for(
                        link_description.get("view"),
                        **link_description.get("params"),
                        _external=self.external_links,
                    ),
                    **link_description.get("kwargs"),  # type: ignore
                }
            )
        return td_links

    def add_link(self, view: Type[View], rel: str, kwargs=None, params=None):
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
        self._links.append(
            {"rel": rel, "view": view, "params": params, "kwargs": kwargs}
        )

    def to_dict(self) -> dict:
        """ """
        td = {
            "@context": [
                "https://www.w3.org/2019/wot/td/v1",
                "https://iot.mozilla.org/schemas/",
            ],
            "@type": current_labthing().types,
            "id": current_labthing().id,
            "title": current_labthing().title,
            "description": current_labthing().description,
            "properties": self.properties,
            "actions": self.actions,
            "events": self.events,
            "links": self.links,
            "securityDefinitions": {"nosec_sc": {"scheme": "nosec"}},
            "security": "nosec_sc",
        }

        if not self.external_links and has_request_context():
            td["base"] = request.host_url

        return td

    def view_to_thing_property(self, rules: list, view: Type[PropertyView]) -> dict:
        """

        :param rules: list:
        :param view: PropertyView:

        """

        # Basic description
        prop_description: Dict[str, Any] = {
            "title": getattr(view, "title", None) or view.__name__,
            "description": getattr(view, "description", None) or get_docstring(view),
            "readOnly": not (
                hasattr(view, "post") or hasattr(view, "put") or hasattr(view, "delete")
            ),
            "writeOnly": not hasattr(view, "get"),
            "forms": view_to_thing_forms(rules, view, external=self.external_links),
            "uriVariables": {},
        }

        semtype = getattr(view, "semtype", None)
        if semtype:
            prop_description["@type"] = semtype

        # Look for a _propertySchema in the Property classes API SPec
        prop_schema = getattr(view, "schema", None)

        if prop_schema:
            # Convert schema to JSON
            prop_schema_json = schema_to_json(prop_schema)

            # Add schema to prop description
            prop_description.update(prop_schema_json)

        # Add URI variables
        for prop_rule in rules:
            params_dict: Dict[str, Any] = {}
            for param in rule_to_params(prop_rule):
                params_dict.update(
                    {
                        param.get("name", {}): {
                            "type": param.get("type")
                            or param.get("schema", {}).get("type")
                        }
                    }
                )
            prop_description["uriVariables"].update(params_dict)
        if not prop_description["uriVariables"]:
            del prop_description["uriVariables"]

        return prop_description

    def view_to_thing_event(self, rules: list, view: Type[EventView]) -> dict:
        """

        :param rules: list:
        :param view: View:

        """

        # Basic description
        event_description: Dict[str, Any] = {
            "title": getattr(view, "title", None) or view.__name__,
            "description": getattr(view, "description", None) or get_docstring(view),
            "forms": view_to_thing_forms(rules, view, external=self.external_links),
        }

        semtype = getattr(view, "semtype", None)
        if semtype:
            event_description["@type"] = semtype

        # Look for a _propertySchema in the Property classes API SPec
        event_schema = getattr(view, "schema", None)

        if event_schema:
            # Convert schema to JSON
            event_schema_json = schema_to_json(event_schema)

            # Add schema to prop description
            event_description["data"] = event_schema_json

        # Add URI variables
        uri_variables: Dict[str, Dict] = {}
        for event_rule in rules:
            params_dict: Dict[str, Any] = {}
            for param in rule_to_params(event_rule):
                params_dict.update(
                    {
                        str(param.get("name")): {
                            "type": param.get("type")
                            or param.get("schema", {}).get("type")
                        }
                    }
                )
            uri_variables.update(params_dict)
        if uri_variables:
            event_description["uriVariables"] = uri_variables

        return event_description

    def view_to_thing_action(self, rules: list, view: Type[ActionView]) -> dict:
        """

        :param rules: list:
        :param view: View:

        """

        # Basic description
        action_description = {
            "title": getattr(view, "title", None) or view.__name__,
            "description": getattr(view, "description", None) or get_docstring(view),
            "safe": getattr(view, "safe", False),
            "idempotent": getattr(view, "idempotent", False),
            "forms": view_to_thing_forms(rules, view, external=self.external_links),
        }

        # Look for a _params in the Action classes API Spec
        action_input_schema = getattr(view, "args", None)
        if action_input_schema:
            # Add schema to prop description
            action_description["input"] = schema_to_json(action_input_schema)

        semtype = getattr(view, "semtype", None)
        if semtype:
            action_description["@type"] = semtype

        # Add schema to prop description
        action_description["output"] = schema_to_json(
            build_action_schema(view.schema, view.args)()
        )

        return action_description

    def property(self, rules: list, view: Type[PropertyView]):
        """

        :param rules: list:
        :param view: View:

        """
        endpoint = getattr(view, "endpoint", None) or getattr(rules[0], "endpoint")
        self.properties[endpoint] = self.view_to_thing_property(rules, view)

    def action(self, rules: list, view: Type[ActionView]):
        """Add a view representing an Action.

        NB at present this will fail for any view that doesn't support POST
        requests.

        :param rules: list:
        :param view: View:

        """
        if not hasattr(view, "post"):
            raise AttributeError(
                f"The API View '{view}' was added as an Action, \
                but it does not have a POST method."
            )
        endpoint = getattr(view, "endpoint", None) or getattr(rules[0], "endpoint")
        self.actions[endpoint] = self.view_to_thing_action(rules, view)

    def event(self, rules: list, view: Type[EventView]):
        """Add a view representing an event queue.

        :param rules: list:
        :param view: View:

        """
        endpoint = getattr(view, "endpoint", None) or getattr(rules[0], "endpoint")
        self.events[endpoint] = self.view_to_thing_event(rules, view)
