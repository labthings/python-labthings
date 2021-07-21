from flask import Blueprint, Response, make_response, render_template

from ...find import current_labthing
from ...views import View


class APISpecView(View):
    """OpenAPI v3 documentation"""

    responses = {
        "200": {
            "description": "OpenAPI v3 description of this API",
            "content": {"application/json": {}},
        }
    }

    def get(self):
        """OpenAPI v3 documentation"""
        return current_labthing().spec.to_dict()


class APISpecYAMLView(View):
    """OpenAPI v3 documentation

    A YAML document containing an API description in OpenAPI format
    """

    responses = {
        "200": {
            "description": "OpenAPI v3 description of this API",
            "content": {"text/yaml": {}},
        }
    }

    def get(self):
        return Response(current_labthing().spec.to_yaml(), mimetype="text/yaml")


class SwaggerUIView(View):
    """Swagger UI documentation"""

    def get(self):
        """ """
        return make_response(render_template("swagger-ui.html"))


docs_blueprint = Blueprint(
    "labthings_docs", __name__, static_folder="./static", template_folder="./templates"
)

docs_blueprint.add_url_rule("/swagger", view_func=APISpecView.as_view("swagger_json"))
docs_blueprint.add_url_rule("/openapi", endpoint="swagger_json")
docs_blueprint.add_url_rule("/openapi.json", endpoint="swagger_json")
docs_blueprint.add_url_rule(
    "/openapi.yaml", view_func=APISpecYAMLView.as_view("openapi_yaml")
)
docs_blueprint.add_url_rule(
    "/swagger-ui", view_func=SwaggerUIView.as_view("swagger_ui")
)
SwaggerUIView.endpoint = "labthings_docs.swagger_ui"
