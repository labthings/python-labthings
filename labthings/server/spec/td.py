from flask import url_for
from apispec import APISpec

from ..view import View

from .utilities import get_spec, convert_schema, schema_to_json
from .paths import rule_to_params, rule_to_path

from ..find import current_labthing

from labthings.core.utilities import get_docstring, snake_to_camel


def find_schema_for_view(view: View):
    """Find the broadest available data schema for a Flask view

    First looks for class-level, then GET, POST, and PUT methods depending on if the
    view is read/write only
    
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
        elif hasattr(view, "put"):
            # Use PUT schema
            prop_schema = get_spec(view.put).get("_params")

    return prop_schema


class ThingDescription:
    def __init__(self, apispec: APISpec):
        self.apispec = apispec
        self.properties = {}
        self.actions = {}
        self.events = {}
        self._links = []
        super().__init__()

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
            "@context": "https://www.w3.org/2019/wot/td/v1",
            "id": url_for("root", _external=True),
            "title": current_labthing().title,
            "description": current_labthing().description,
            "properties": self.properties,
            "actions": self.actions,
            "links": self.links,
        }

    def view_to_thing_property(self, rules: list, view: View):
        prop_urls = [rule_to_path(rule) for rule in rules]

        # Basic description
        prop_description = {
            "title": view.__name__,
            "description": (
                get_spec(view).get("description")
                or get_docstring(view)
                or (get_docstring(view.get) if hasattr(view, "get") else "")
            ),
            "readOnly": not (
                hasattr(view, "post") or hasattr(view, "put") or hasattr(view, "delete")
            ),
            "writeOnly": not hasattr(view, "get"),
            # TODO: Make URLs absolute
            "links": [{"href": f"{url}"} for url in prop_urls],
            "uriVariables": {},
        }

        # Look for a _propertySchema in the Property classes API SPec
        prop_schema = get_spec(view).get("_propertySchema")
        # If no class-level property schema was found
        if not prop_schema:
            prop_schema = find_schema_for_view(view)

        if prop_schema:
            # Ensure valid schema type
            prop_schema = convert_schema(prop_schema, self.apispec)

            # Convert schema to JSON
            prop_schema_json = schema_to_json(prop_schema, self.apispec)

            # Add schema to prop description
            prop_description.update(prop_schema_json)

        # Add URI variables
        for prop_rule in rules:
            params_dict = {}
            for param in rule_to_params(prop_rule):
                params_dict.update({param.get("name"): {"type": param.get("type")}})
            prop_description["uriVariables"].update(params_dict)
        if not prop_description["uriVariables"]:
            del prop_description["uriVariables"]

        return prop_description

    def view_to_thing_action(self, rules: list, view: View):
        action_urls = [rule_to_path(rule) for rule in rules]

        # Basic description
        action_description = {
            "title": view.__name__,
            "description": get_spec(view).get("description")
            or get_docstring(view)
            or (get_docstring(view.post) if hasattr(view, "post") else ""),
            # TODO: Make URLs absolute
            "links": [{"href": f"{url}"} for url in action_urls],
        }

        return action_description

    def property(self, rules: list, view: View):
        key = snake_to_camel(view.endpoint)
        self.properties[key] = self.view_to_thing_property(rules, view)

    def action(self, rules: list, view: View):
        key = snake_to_camel(view.endpoint)
        self.actions[key] = self.view_to_thing_action(rules, view)
