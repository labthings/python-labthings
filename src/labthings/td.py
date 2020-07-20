from flask import url_for, request

from .views import View
from .event import Event
from .json.schemas import schema_to_json, rule_to_params, rule_to_path
from .find import current_labthing
from .utilities import get_docstring, snake_to_camel


def view_to_thing_action_forms(rules: list, view: View):
    """Build a W3C form description for an ActionView

    :param rules: List of Flask rules
    :type rules: list
    :param view: View class
    :type view: View
    :param rules: list: 
    :param view: View: 
    :returns: Form description
    :rtype: [dict]

    """
    forms = []

    # HTTP invokeaction requires POST method
    if hasattr(view, "post"):
        prop_urls = [rule_to_path(rule) for rule in rules]

        # Get input content_type
        content_type = getattr(view, "content_type", "application/json")
        response_content_type = getattr(
            view, "response_content_type", "application/json"
        )

        for url in prop_urls:
            form = {
                "op": "invokeaction",
                "htv:methodName": "POST",
                "href": url,
                "contentType": content_type,
            }
            if response_content_type != content_type:
                form["response"] = {"contentType": response_content_type}

            forms.append(form)

    return forms


def view_to_thing_property_forms(rules: list, view: View):
    """Build a W3C form description for a PropertyView

    :param rules: List of Flask rules
    :type rules: list
    :param view: View class
    :type view: View
    :param rules: list: 
    :param view: View: 
    :returns: Form description
    :rtype: [dict]

    """
    forms = []

    # Get basic information
    prop_urls = [rule_to_path(rule) for rule in rules]

    # Get input content_type
    content_type = getattr(view, "content_type", "application/json")

    # HTTP readproperty requires GET method
    if hasattr(view, "get"):
        for url in prop_urls:
            form = {
                "op": "readproperty",
                "htv:methodName": "GET",
                "href": url,
                "contentType": content_type,
            }
            forms.append(form)

    # HTTP writeproperty requires PUT method
    if hasattr(view, "put"):
        for url in prop_urls:
            form = {
                "op": "writeproperty",
                "htv:methodName": "PUT",
                "href": url,
                "contentType": content_type,
            }
            forms.append(form)

    # HTTP writeproperty may use POST method
    elif hasattr(view, "post"):
        for url in prop_urls:
            form = {
                "op": "writeproperty",
                "htv:methodName": "POST",
                "href": url,
                "contentType": content_type,
            }
            forms.append(form)

    return forms


class ThingDescription:
    """ """
    def __init__(self):
        self.properties = {}
        self.actions = {}
        self.events = {}
        self._links = []
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
                        _external=True,
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
        """

        :param event: Event: 

        """
        # TODO: Include event schema
        return {"forms": []}

    def view_to_thing_property(self, rules: list, view: View):
        """

        :param rules: list: 
        :param view: View: 

        """
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

    def view_to_thing_action(self, rules: list, view: View):
        """

        :param rules: list: 
        :param view: View: 

        """
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

    def property(self, rules: list, view: View):
        """

        :param rules: list: 
        :param view: View: 

        """
        endpoint = getattr(view, "endpoint", None) or getattr(rules[0], "endpoint")
        key = snake_to_camel(endpoint)
        self.properties[key] = self.view_to_thing_property(rules, view)

    def action(self, rules: list, view: View):
        """Add a view representing an Action.
        
        NB at present this will fail for any view that doesn't support POST
        requests.

        :param rules: list: 
        :param view: View: 

        """
        if not hasattr(view, "post"):
            raise AttributeError(
                f"The API View '{view}' was added as an Action, but it does not have a POST method."
            )
        endpoint = getattr(view, "endpoint", None) or getattr(rules[0], "endpoint")
        key = snake_to_camel(endpoint)
        self.actions[key] = self.view_to_thing_action(rules, view)

    def event(self, event: Event):
        """

        :param event: Event: 

        """
        self.events[event.name] = self.event_to_thing_event(event)
