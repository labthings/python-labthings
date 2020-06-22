from flask import url_for, request
from apispec import APISpec
import weakref

from ..view import View
from ..event import Event

from .utilities import (
    get_spec,
    convert_to_schema_or_json,
    schema_to_json,
    get_semantic_type,
)
from .paths import rule_to_params, rule_to_path

from ..find import current_labthing

from labthings.core.utilities import get_docstring, snake_to_camel


def find_schema_for_view(view: View):
    """Find the broadest available data schema for a Flask view

    Looks for GET, POST, and PUT methods depending on if the view is read/write only
    
    Args:
        view (View): View to search for schema
    
    Returns:
        Broadest available schema dictionary for the View. Returns empty dictionary
            if no schema is found
    """
    prop_schema = {}
    # If prop is read-only
    if hasattr(view, "get") and not (hasattr(view, "post") or hasattr(view, "put")):
        # Use GET schema
        prop_schema = get_spec(view.get).get("_schema", {}).get(200)
    # If prop is write-only
    elif not hasattr(view, "get") and (hasattr(view, "post") or hasattr(view, "put")):
        if hasattr(view, "post"):
            # Use POST schema
            prop_schema = get_spec(view.post).get("_params")
        else:
            # Use PUT schema
            prop_schema = get_spec(view.put).get("_params")
    else:
        prop_schema = {}

    return prop_schema


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
            "@context": ["https://iot.mozilla.org/schemas/"],
            "@type": current_labthing().types,
            "id": url_for("root", _external=True),
            "base": request.host_url,
            "title": current_labthing().title,
            "description": current_labthing().description,
            "properties": self.properties,
            "actions": self.actions,
            "events": self.events,  # TODO: Enable once properly populated
            "links": self.links,
        }

    def event_to_thing_event(self, event: Event):
        # TODO: Include event schema
        return {}

    def view_to_thing_property(self, rules: list, view: View):
        prop_urls = [rule_to_path(rule) for rule in rules]

        # Basic description
        prop_description = {
            "title": getattr(view, "title", None) or view.__name__,
            "description": get_docstring(view),
            "readOnly": not (
                hasattr(view, "post") or hasattr(view, "put") or hasattr(view, "delete")
            ),
            "writeOnly": not hasattr(view, "get"),
            "links": [{"href": f"{url}"} for url in prop_urls],
            "uriVariables": {},
            **get_semantic_type(view),
        }

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
            "description": get_docstring(view),
            "links": [{"href": f"{url}"} for url in action_urls],
            "safe": getattr(view, "safe", False),
            "idempotent": getattr(view, "idempotent", False),
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
            action_description["input"].update(get_semantic_type(view))

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
