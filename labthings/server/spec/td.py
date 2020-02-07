from flask import url_for
from apispec import APISpec

from ..view import View

from .utilities import get_spec, convert_schema, schema_to_json
from .paths import rule_to_params, rule_to_path

from ..find import current_labthing

from labthings.core.utilities import get_docstring


def find_schema_for_view(view: View):
    prop_schema = {}
    # If prop is read-only
    if hasattr(view, "get") and not (hasattr(view, "post") or hasattr(view, "put")):
        # Use GET schema
        prop_schema = get_spec(view.get).get("_schema").get(200)
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
        self.properties = []
        self.actions = []
        self.events = []
        super().__init__()

    def to_dict(self):
        return {
            "@context": "https://www.w3.org/2019/wot/td/v1",
            "id": url_for("labthings_docs.w3c_td", _external=True),
            "title": current_labthing().title,
            "description": current_labthing().description,
            "properties": self.properties,
            "actions": self.actions,
        }

    def view_to_thing_property(self, rules: list, view: View):
        prop_urls = [rule_to_path(rule) for rule in rules]

        # Basic description
        prop_description = {
            "title": view.__name__,
            "description": (
                get_docstring(view)
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
            "description": get_docstring(view)
            or (get_docstring(view.post) if hasattr(view, "post") else ""),
            # TODO: Make URLs absolute
            "links": [{"href": f"{url}"} for url in action_urls],
        }

        return action_description

    def property(self, rules: list, view: View):
        self.properties.append(self.view_to_thing_property(rules, view))

    def action(self, rules: list, view: View):
        self.properties.append(self.view_to_thing_action(rules, view))
