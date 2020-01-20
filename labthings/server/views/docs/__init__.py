from flask import (
    url_for,
    jsonify,
    render_template,
    Blueprint,
    current_app,
    request,
    make_response,
)

from labthings.core.utilities import get_docstring

from ...view import View
from ...find import current_labthing
from ...spec import get_spec, rule_to_path, rule_to_params, convert_schema, schema2json


class APISpecView(View):
    """
    OpenAPI v3 documentation
    """

    def get(self):
        """
        OpenAPI v3 documentation
        """
        return jsonify(current_labthing().spec.to_dict())


class SwaggerUIView(View):
    """
    Swagger UI documentation
    """

    def get(self):
        return make_response(render_template("swagger-ui.html"))


class W3CThingDescriptionView(View):
    """
    W3C-style Thing Description
    """

    def get(self):
        base_url = request.host_url.rstrip("/")

        swag = current_labthing().spec

        props = {}
        for key, prop in current_labthing().properties.items():
            props[key] = {}
            prop_rules = current_app.url_map._rules_by_endpoint.get(prop.endpoint)
            prop_urls = [rule_to_path(rule) for rule in prop_rules]

            # Look for a _propertySchema in the Property classes API SPec
            prop_spec = get_spec(prop)
            prop_schema = convert_schema(prop_spec.get("_propertySchema"), swag)
            if not prop_schema:
                # If prop is read-only
                if hasattr(prop, "get") and not (
                    hasattr(prop, "post") or hasattr(prop, "put")
                ):
                    prop_schema = convert_schema(
                        get_spec(prop.get).get("_schema").get(200), swag
                    )
                # If prop is write-only
                elif not hasattr(prop, "get") and (
                    hasattr(prop, "post") or hasattr(prop, "put")
                ):
                    if hasattr(prop, "post"):
                        prop_schema = convert_schema(
                            get_spec(prop.post).get("_params"), swag
                        )
                    elif hasattr(prop, "put"):
                        prop_schema = convert_schema(
                            get_spec(prop.put).get("_params"), swag
                        )
                    else:
                        prop_schema = {}

            prop_json_schema = schema2json(prop_schema, current_labthing().spec)

            props[key].update(prop_json_schema)

            # Generate the rest of the description
            props[key]["title"] = prop.__name__
            props[key]["description"] = (
                props[key].get("description")
                or get_docstring(prop)
                or (get_docstring(prop.get) if hasattr(prop, "get") else "")
            )
            props[key]["readOnly"] = not (
                hasattr(prop, "post") or hasattr(prop, "put") or hasattr(prop, "delete")
            )
            props[key]["writeOnly"] = not hasattr(prop, "get")
            props[key]["links"] = [{"href": f"{base_url}{url}"} for url in prop_urls]

            props[key]["uriVariables"] = {}
            for prop_rule in prop_rules:
                params = rule_to_params(prop_rule)
                params_dict = {}
                for param in params:
                    params_dict.update({param.get("name"): {"type": param.get("type")}})
                props[key]["uriVariables"].update(params_dict)
            if not props[key]["uriVariables"]:
                del props[key]["uriVariables"]

        actions = {}
        for key, action in current_labthing().actions.items():
            action_rules = current_app.url_map._rules_by_endpoint.get(action.endpoint)
            action_urls = [rule_to_path(rule) for rule in action_rules]

            actions[key] = {}
            actions[key]["title"] = action.__name__
            # TODO: Get description from __apispec__ preferentially
            actions[key]["description"] = get_docstring(action) or (
                get_docstring(action.post) if hasattr(action, "post") else ""
            )
            actions[key]["links"] = [
                {"href": f"{base_url}{url}"} for url in action_urls
            ]

        td = {
            "@context": "https://www.w3.org/2019/wot/td/v1",
            "id": url_for("labthings_docs.w3c_td", _external=True),
            "title": current_labthing().title,
            "description": current_labthing().description,
            "properties": props,
            "actions": actions,
        }

        return jsonify(td)


docs_blueprint = Blueprint(
    "labthings_docs", __name__, static_folder="./static", template_folder="./templates"
)

docs_blueprint.add_url_rule("/swagger", view_func=APISpecView.as_view("swagger_json"))
docs_blueprint.add_url_rule(
    "/swagger-ui", view_func=SwaggerUIView.as_view("swagger_ui")
)
docs_blueprint.add_url_rule("/td", view_func=W3CThingDescriptionView.as_view("w3c_td"))
