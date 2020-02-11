from flask import render_template, Blueprint, make_response

from ...view import View
from ...find import current_labthing


class APISpecView(View):
    """OpenAPI v3 documentation"""

    def get(self):
        """OpenAPI v3 documentation"""
        return current_labthing().spec.to_dict()


class SwaggerUIView(View):
    """Swagger UI documentation"""

    def get(self):
        return make_response(render_template("swagger-ui.html"))


class W3CThingDescriptionView(View):
    """W3C-style Thing Description"""

    def get(self):
        return current_labthing().thing_description.to_dict()


docs_blueprint = Blueprint(
    "labthings_docs", __name__, static_folder="./static", template_folder="./templates"
)

docs_blueprint.add_url_rule("/swagger", view_func=APISpecView.as_view("swagger_json"))
docs_blueprint.add_url_rule(
    "/swagger-ui", view_func=SwaggerUIView.as_view("swagger_ui")
)
docs_blueprint.add_url_rule("/td", view_func=W3CThingDescriptionView.as_view("w3c_td"))
