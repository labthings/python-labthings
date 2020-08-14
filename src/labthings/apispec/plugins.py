from apispec.ext.marshmallow import MarshmallowPlugin as _MarshmallowPlugin
from apispec.ext.marshmallow import OpenAPIConverter
import re

from flask.views import http_method_funcs

from apispec import BasePlugin

from ..utilities import merge
from ..interactions import Interaction, Property, Action
from ..json.schemas import schema_to_json
from ..schema import build_action_schema
from .. import fields


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
    def spec_for_interaction(cls, interaction: Interaction):
        d = {}

        for meth, op in getattr(interaction, "_methodmap", {}).items():
            if meth in http_method_funcs and hasattr(interaction, op):
                d[meth] = {
                    "description": interaction.description,
                    "summary": interaction.summary,
                    "tags": interaction.tags,
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
    def spec_for_property(cls, prop: Property):
        base_d = cls.spec_for_interaction(prop)

        class_json_schema = schema_to_json(prop.schema) if prop.schema else None

        prop_d = {}

        for meth, op in getattr(prop, "_methodmap", {}).items():
            if op and meth in http_method_funcs and hasattr(prop, op):
                if op == "readproperty":
                    prop_d[meth] = {
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
                    }
                elif op == "writeproperty":
                    prop_d[meth] = {
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
                    }

        final_d = merge(base_d, prop_d)

        return final_d

    @classmethod
    def spec_for_action(cls, action: Action):
        base_d = cls.spec_for_interaction(action)

        class_args = schema_to_json(action.args)
        action_json_schema = schema_to_json(
            build_action_schema(action.schema, action.args)()
        )
        queue_json_schema = schema_to_json(
            build_action_schema(action.schema, action.args)(many=True)
        )

        action_d = {
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
                }
            }
        }
        for meth, op in getattr(action, "_methodmap", {}).items():
            if (
                op
                and op == "invokeaction"
                and meth in http_method_funcs
                and hasattr(action, op)
            ):
                action_d[meth] = {
                    "requestBody": {
                        "content": {
                            action.content_type: (
                                {"schema": class_args} if class_args else {}
                            )
                        }
                    },
                    "responses": {
                        # Responses like images must be added as 200 responses with cls.responses = {200: {...}}
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
                }

        final_d = merge(base_d, action_d)

        return final_d

    def operation_helper(self, path, operations, **kwargs):
        """Path helper that allows passing a Flask view function."""
        # rule = self._rule_for_view(interaction.dispatch_request, app=app)
        interaction = kwargs.pop("interaction", None)
        ops = {}
        if isinstance(interaction, Property):
            ops = self.spec_for_property(interaction)
        elif isinstance(interaction, Action):
            ops = self.spec_for_action(interaction)
        operations.update(ops)
