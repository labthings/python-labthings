import re

from apispec import BasePlugin
from apispec.ext.marshmallow import MarshmallowPlugin as _MarshmallowPlugin
from apispec.ext.marshmallow import OpenAPIConverter
from flask.views import http_method_funcs

from .. import fields
from ..json.schemas import schema_to_json
from ..schema import build_action_schema, EventSchema
from ..utilities import get_docstring, get_summary, merge
from ..views import ActionView, PropertyView, EventView, View


class ExtendedOpenAPIConverter(OpenAPIConverter):
    """ """

    field_mapping = OpenAPIConverter.field_mapping

    def init_attribute_functions(self, *args, **kwargs):
        """
        :param *args:
        :param **kwargs:
        """
        OpenAPIConverter.init_attribute_functions(self, *args, **kwargs)
        self.attribute_functions.append(self.jsonschema_type_mapping)

    def jsonschema_type_mapping(self, field, **kwargs):
        """
        :param field:
        :param **kwargs:
        """
        ret = {}
        if hasattr(field, "_jsonschema_type_mapping"):
            schema = field._jsonschema_type_mapping()
            ret.update(schema)
        return ret


class MarshmallowPlugin(_MarshmallowPlugin):
    """ """

    Converter = ExtendedOpenAPIConverter


# from flask-restplus
RE_URL = re.compile(r"<(?:[^:<>]+:)?([^<>]+)>")


class FlaskLabThingsPlugin(BasePlugin):
    """APIspec plugin for Flask LabThings"""

    @classmethod
    def spec_for_interaction(cls, interaction):
        d = {}

        for method in http_method_funcs:
            if hasattr(interaction, method):
                d[method] = {
                    "description": getattr(interaction, "description", None)
                    or get_docstring(interaction),
                    "summary": getattr(interaction, "summary", None)
                    or get_summary(interaction),
                    "tags": list(interaction.get_tags()),
                    "responses": {
                        "default": {
                            "description": "Unexpected error",
                            "content": {
                                "application/json": {
                                    "schema": schema_to_json(
                                        {
                                            "code": fields.Integer(),
                                            "message": fields.String(),
                                            "name": fields.String(),
                                        }
                                    )
                                }
                            },
                        }
                    },
                }
        return d

    @classmethod
    def spec_for_property(cls, prop):
        class_json_schema = schema_to_json(prop.schema) if prop.schema else None

        d = cls.spec_for_interaction(prop)

        # Add in writeproperty methods
        for method in ("put", "post"):
            if hasattr(prop, method):
                d[method] = merge(
                    d.get(method, {}),
                    {
                        "requestBody": {
                            "content": {
                                prop.content_type: (
                                    {"schema": class_json_schema}
                                    if class_json_schema
                                    else {}
                                )
                            }
                        },
                        "responses": {
                            200: {
                                "content": {
                                    prop.content_type: (
                                        {"schema": class_json_schema}
                                        if class_json_schema
                                        else {}
                                    )
                                },
                                "description": "Write property",
                            }
                        },
                    },
                )

        # Add in readproperty methods
        if hasattr(prop, "get"):
            d["get"] = merge(
                d.get("get", {}),
                {
                    "responses": {
                        200: {
                            "content": {
                                prop.content_type: (
                                    {"schema": class_json_schema}
                                    if class_json_schema
                                    else {}
                                )
                            },
                            "description": "Read property",
                        }
                    },
                },
            )

        # Enable custom responses from all methods
        for method in d.keys():
            d[method]["responses"].update(prop.responses)

        return d

    @classmethod
    def spec_for_action(cls, action):
        class_args = schema_to_json(action.args)
        action_json_schema = schema_to_json(
            build_action_schema(action.schema, action.args)()
        )
        queue_json_schema = schema_to_json(
            build_action_schema(action.schema, action.args)(many=True)
        )

        d = cls.spec_for_interaction(action)

        # Add in Action spec
        d = merge(
            d,
            {
                "post": {
                    "requestBody": {
                        "content": {
                            action.content_type: (
                                {"schema": class_args} if class_args else {}
                            )
                        }
                    },
                    "responses": {
                        # Responses like images must be added as
                        # 200 responses with cls.responses = {200: {...}}
                        200: {
                            "description": "Action completed immediately",
                            # Allow customising 200 (immediate response) content type
                            "content": {
                                action.response_content_type: (
                                    {"schema": action_json_schema}
                                    if action_json_schema
                                    else {}
                                )
                            },
                        },
                        201: {
                            "description": "Action started",
                            # Our POST 201 MUST be application/json
                            "content": {
                                "application/json": (
                                    {"schema": action_json_schema}
                                    if action_json_schema
                                    else {}
                                )
                            },
                        },
                    },
                },
                "get": {
                    "responses": {
                        # Our GET 200 MUST be application/json
                        200: {
                            "description": "Action queue",
                            "content": {
                                "application/json": (
                                    {"schema": queue_json_schema}
                                    if queue_json_schema
                                    else {}
                                )
                            },
                        }
                    },
                },
            },
        )
        # Enable custom responses from POST
        d["post"]["responses"].update(action.responses)
        return d

    @classmethod
    def spec_for_event(cls, event):
        class_json_schema = schema_to_json(event.schema) if event.schema else None
        queue_json_schema = schema_to_json(EventSchema(many=True))
        if class_json_schema:
            queue_json_schema["properties"]["data"] = class_json_schema

        d = cls.spec_for_interaction(event)

        # Add in Action spec
        d = merge(
            d,
            {
                "get": {
                    "responses": {
                        200: {
                            "description": "Event queue",
                            "content": {
                                "application/json": (
                                    {"schema": queue_json_schema}
                                    if queue_json_schema
                                    else {}
                                )
                            },
                        }
                    },
                },
            },
        )
        return d

    def operation_helper(self, path, operations, **kwargs):
        """Path helper that allows passing a Flask view function."""
        # rule = self._rule_for_view(interaction.dispatch_request, app=app)
        interaction = kwargs.pop("interaction", None)
        ops = {}
        if issubclass(interaction, PropertyView):
            ops = self.spec_for_property(interaction)
        elif issubclass(interaction, ActionView):
            ops = self.spec_for_action(interaction)
        elif issubclass(interaction, EventView):
            ops = self.spec_for_event(interaction)
        elif issubclass(interaction, View):
            ops = self.spec_for_interaction(interaction)
        operations.update(ops)
