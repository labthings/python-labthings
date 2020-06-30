from flask import url_for, request
from apispec import APISpec
import weakref

from ..view import View
from ..event import Event

from .utilities import (
    convert_to_schema_or_json,
    schema_to_json,
)
from .paths import rule_to_params, rule_to_path

from ..find import current_labthing

from labthings.core.utilities import get_docstring, snake_to_camel


def build_forms_for_view(rules: list, view: View, op: list):
    """Build a W3C form description for a particular View

    Args:
        rules (list): List of Flask rules
        view (View): View class
        op (list): List of Form operations

    Returns:
        [dict]: Form description
    """
    forms = []
    prop_urls = [rule_to_path(rule) for rule in rules]

    content_type = getattr(view, "content_type", None) or "application/json"

    for url in prop_urls:
        forms.append({"op": op, "href": url, "contentType": content_type})

    return forms


def view_to_thing_property_forms(rules: list, view: View):
    """Build a W3C form description for a PropertyView

    Args:
        rules (list): List of Flask rules
        view (View): View class
        op (list): List of Form operations

    Returns:
        [dict]: Form description
    """
    readable = hasattr(view, "post") or hasattr(view, "put") or hasattr(view, "delete")
    writeable = hasattr(view, "get")

    op = []
    if readable:
        op.append("readproperty")
    if writeable:
        op.append("writeproperty")

    return build_forms_for_view(rules, view, op=op)


def view_to_thing_action_forms(rules: list, view: View):
    """Build a W3C form description for an ActionView

    Args:
        rules (list): List of Flask rules
        view (View): View class
        op (list): List of Form operations

    Returns:
        [dict]: Form description
    """
    return build_forms_for_view(rules, view, op=["invokeaction"])


class ThingDescription:
    def __init__(self, apispec: APISpec):
        self._apispec = weakref.ref(apispec)
        self.properties = {}
        self.actions = {}
        self.events = {}
        self._links = []
        super().__init__()

    @property
    def apispec(self):
        return self._apispec()

    @property
    def links(self):
        td_links = []
        for link_description in self._links:
            td_links.append(
                {
                    "rel": link_description.get("rel"),
                    "href": current_labthing().url_for(
                        link_description.get("view"),
                        **link_description.get("params"),
                        _external=True,
                    ),
                    **link_description.get("kwargs"),
                }
            )
        return td_links

    def add_link(self, view, rel, kwargs=None, params=None):
        if kwargs is None:
            kwargs = {}
        if params is None:
            params = {}
        self._links.append(
            {"rel": rel, "view": view, "params": params, "kwargs": kwargs}
        )

    def to_dict(self):
        return {
            "@context": [
                "https://www.w3.org/2019/wot/td/v1",
                "https://iot.mozilla.org/schemas/",
            ],
            "@type": current_labthing().types,
            "id": url_for("root", _external=True),
            "base": request.host_url,
            "title": current_labthing().title,
            "description": current_labthing().description,
            "properties": self.properties,
            "actions": self.actions,
            # "events": self.events,  # TODO: Enable once properly populated
            "links": self.links,
            "securityDefinitions": {"nosec_sc": {"scheme": "nosec"}},
            "security": "nosec_sc",
        }

    def event_to_thing_event(self, event: Event):
        # TODO: Include event schema
        return {"forms": []}

    def view_to_thing_property(self, rules: list, view: View):
        prop_urls = [rule_to_path(rule) for rule in rules]

        # Basic description
        prop_description = {
            "title": getattr(view, "title", None) or view.__name__,
            "description": getattr(view, "description", None) or get_docstring(view),
            "readOnly": not (
                hasattr(view, "post") or hasattr(view, "put") or hasattr(view, "delete")
            ),
            "writeOnly": not hasattr(view, "get"),
            "links": [{"href": f"{url}"} for url in prop_urls],
            "forms": view_to_thing_property_forms(rules, view),
            "uriVariables": {},
        }

        semtype = getattr(view, "semtype")
        if semtype:
            prop_description["@type"] = semtype

        # Look for a _propertySchema in the Property classes API SPec
        prop_schema = getattr(view, "schema", None)

        if prop_schema:
            # Ensure valid schema type
            prop_schema = convert_to_schema_or_json(prop_schema, self.apispec)

            # Convert schema to JSON
            prop_schema_json = schema_to_json(prop_schema, self.apispec)

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

    def view_to_thing_action(self, rules: list, view: View):
        action_urls = [rule_to_path(rule) for rule in rules]

        # Basic description
        action_description = {
            "title": getattr(view, "title", None) or view.__name__,
            "description": getattr(view, "description", None) or get_docstring(view),
            "links": [{"href": f"{url}"} for url in action_urls],
            "safe": getattr(view, "safe", False),
            "idempotent": getattr(view, "idempotent", False),
            "forms": view_to_thing_action_forms(rules, view),
        }

        # Look for a _params in the Action classes API Spec
        action_input_schema = getattr(view, "args", None)
        if action_input_schema:
            # Ensure valid schema type
            action_input_schema = convert_to_schema_or_json(
                action_input_schema, self.apispec
            )
            # Add schema to prop description
            action_description["input"] = schema_to_json(
                action_input_schema, self.apispec
            )

        semtype = getattr(view, "semtype")
        if semtype:
            action_description["@type"] = semtype

        # Look for a _schema in the Action classes API Spec
        action_output_schema = getattr(view, "schema", None)
        if action_output_schema:
            # Ensure valid schema type
            action_output_schema = convert_to_schema_or_json(
                action_output_schema, self.apispec
            )
            # Add schema to prop description
            action_description["output"] = schema_to_json(
                action_output_schema, self.apispec
            )

        return action_description

    def property(self, rules: list, view: View):
        endpoint = getattr(view, "endpoint", None) or getattr(rules[0], "endpoint")
        key = snake_to_camel(endpoint)
        self.properties[key] = self.view_to_thing_property(rules, view)

    def action(self, rules: list, view: View):
        """Add a view representing an Action.

        NB at present this will fail for any view that doesn't support POST
        requests.
        """
        if not hasattr(view, "post"):
            raise AttributeError(
                f"The API View '{view}' was added as an Action, but it does not have a POST method."
            )
        endpoint = getattr(view, "endpoint", None) or getattr(rules[0], "endpoint")
        key = snake_to_camel(endpoint)
        self.actions[key] = self.view_to_thing_action(rules, view)

    def event(self, event: Event):
        self.events[event.name] = self.event_to_thing_event(event)
