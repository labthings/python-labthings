from flask import url_for, request, has_request_context

from .views import Interaction, Property, Action
from .json.schemas import schema_to_json, rule_to_params, rule_to_path
from .find import current_labthing
from .utilities import ResourceURL


def interaction_to_thing_forms(rules: list, view: Interaction, external: bool = True):
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
    for meth, op in getattr(view, "_methodmap", {}).items():
        if op and hasattr(view, op):
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
                # Fix URL for the View's websocket method
                if meth.upper() == "WEBSOCKET":
                    form["href"] = ResourceURL(url, external=external, protocol="ws")
                # Add HTTP methods for non-websocket forms
                else:
                    form["htv:methodName"] = meth.upper()
                    form["href"] = ResourceURL(url, external=external)

                forms.append(form)

    return forms


class ThingDescription:
    """ """

    def __init__(self, external_links: bool = True):
        # Public attributes
        self.properties = {}
        self.actions = {}
        self.events = {}

        # Private attributes
        self._links = []

        # Settings
        self.external_links = external_links

        # Init
        super().__init__()

    @property
    def links(self):
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
                    **link_description.get("kwargs"),
                }
            )
        return td_links

    def add_link(self, view, rel, kwargs=None, params=None):
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

    def to_dict(self):
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
            # "events": self.events,  # TODO: Enable once properly populated
            "links": self.links,
            "securityDefinitions": {"nosec_sc": {"scheme": "nosec"}},
            "security": "nosec_sc",
        }

        if not self.external_links and has_request_context():
            td["base"] = request.host_url

        return td

    def interaction_to_thing_property(self, rules: list, view: Interaction):
        """

        :param rules: list: 
        :param view: View: 

        """
        prop_urls = [rule_to_path(rule) for rule in rules]

        # Basic description
        prop_description = {
            "title": view.title,
            "description": view.description,
            "readOnly": view.readonly,
            "links": [
                {"href": ResourceURL(url, external=self.external_links)}
                for url in prop_urls
            ],
            "forms": interaction_to_thing_forms(
                rules, view, external=self.external_links
            ),
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
            params_dict = {}
            for param in rule_to_params(prop_rule):
                params_dict.update(
                    {
                        param.get("name"): {
                            "type": param.get("type") or param.get("schema").get("type")
                        }
                    }
                )
            prop_description["uriVariables"].update(params_dict)
        if not prop_description["uriVariables"]:
            del prop_description["uriVariables"]

        return prop_description

    def interaction_to_thing_action(self, rules: list, view: Interaction):
        """

        :param rules: list: 
        :param view: View: 

        """
        action_urls = [rule_to_path(rule) for rule in rules]

        # Basic description
        action_description = {
            "title": view.title,
            "description": view.description,
            "links": [
                {"href": ResourceURL(url, external=self.external_links)}
                for url in action_urls
            ],
            "safe": getattr(view, "safe", False),
            "idempotent": getattr(view, "idempotent", False),
            "forms": interaction_to_thing_forms(
                rules, view, external=self.external_links
            ),
        }

        # Look for a _params in the Action classes API Spec
        action_input_schema = getattr(view, "args", None)
        if action_input_schema:
            # Add schema to prop description
            action_description["input"] = schema_to_json(action_input_schema)

        semtype = getattr(view, "semtype", None)
        if semtype:
            action_description["@type"] = semtype

        # Look for a _schema in the Action classes API Spec
        action_output_schema = getattr(view, "schema", None)
        if action_output_schema:
            # Add schema to prop description
            action_description["output"] = schema_to_json(action_output_schema)

        return action_description

    def add(self, rules: list, interaction: Interaction):
        if isinstance(interaction, Property):
            self.properties[interaction.name] = self.interaction_to_thing_property(
                rules, interaction
            )
        elif isinstance(interaction, Action):
            self.actions[interaction.name] = self.interaction_to_thing_action(
                rules, interaction
            )
