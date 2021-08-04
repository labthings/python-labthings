import re
from copy import deepcopy

from apispec import BasePlugin
from apispec.ext.marshmallow import MarshmallowPlugin as _MarshmallowPlugin
from apispec.ext.marshmallow import OpenAPIConverter
from flask.views import http_method_funcs

from .. import fields
from ..json.schemas import schema_to_json
from ..schema import ActionSchema, EventSchema
from ..utilities import get_docstring, get_summary, merge
from ..views import ActionView, EventView, PropertyView, View
from .utilities import ensure_schema, get_marshmallow_plugin


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

    def jsonschema_type_mapping(self, field, **_):
        """
        :param field:
        :param **kwargs:
        """
        ret = {}
        if hasattr(field, "_jsonschema_type_mapping"):
            # pylint: disable=protected-access
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

    spec = None

    def init_spec(self, spec):
        self.spec = spec
        return super().init_spec(spec)

    @classmethod
    def spec_for_interaction(cls, interaction):
        d = {}

        for method in http_method_funcs:
            if hasattr(interaction, method):
                prop = getattr(interaction, method)
                d[method] = {
                    "description": (
                        getattr(prop, "description", None)
                        or get_docstring(prop, remove_newlines=False)
                        or getattr(interaction, "description", None)
                        or get_docstring(interaction, remove_newlines=False)
                    ),
                    "summary": (
                        getattr(prop, "summary", None)
                        or get_summary(prop)
                        or getattr(interaction, "summary", None)
                        or get_summary(interaction)
                    ),
                    "tags": list(interaction.get_tags()),
                    "responses": {
                        "5XX": {
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
                    "parameters": [],
                }
                # Allow custom responses from the class, overridden by the method
                d[method]["responses"].update(
                    deepcopy(getattr(interaction, "responses", {}))
                )
                d[method]["responses"].update(deepcopy(getattr(prop, "responses", {})))
                # Allow custom parameters from the class & method
                d[method]["parameters"].extend(
                    deepcopy(getattr(interaction, "parameters", {}))
                )
                d[method]["parameters"].extend(
                    deepcopy(getattr(prop, "parameters", {}))
                )
        return d

    def spec_for_property(self, prop):
        class_schema = ensure_schema(self.spec, prop.schema) or {}

        d = self.spec_for_interaction(prop)

        # Add in writeproperty methods
        for method in ("put", "post"):
            if hasattr(prop, method):
                d[method] = merge(
                    d.get(method, {}),
                    {
                        "requestBody": {
                            "content": {prop.content_type: {"schema": class_schema}}
                        },
                        "responses": {
                            200: {
                                "content": {
                                    prop.content_type: {"schema": class_schema}
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
                            "content": {prop.content_type: {"schema": class_schema}},
                            "description": "Read property",
                        }
                    },
                },
            )

        return d

    def spec_for_action(self, action):
        action_input = ensure_schema(
            self.spec, action.args, name=f"{action.__name__}InputSchema"
        )
        action_output = ensure_schema(
            self.spec, action.schema, name=f"{action.__name__}OutputSchema"
        )
        # We combine input/output parameters with ActionSchema using an
        # allOf directive, so we don't end up duplicating the schema
        # for every action.
        if action_output or action_input:
            # It would be neater to combine the schemas in OpenAPI with allOf
            # I think the code below does it - but I'm not yet convinced it is working
            # TODO: add tests to validate this
            plugin = get_marshmallow_plugin(self.spec)
            action_input_dict = (
                plugin.resolver.resolve_schema_dict(action_input)
                if action_input
                else {}
            )
            action_output_dict = (
                plugin.resolver.resolve_schema_dict(action_output)
                if action_output
                else {}
            )
            action_schema = {
                "allOf": [
                    plugin.resolver.resolve_schema_dict(ActionSchema),
                    {
                        "type": "object",
                        "properties": {
                            "input": action_input_dict,
                            "output": action_output_dict,
                        },
                    },
                ]
            }
            # The line below builds an ActionSchema subclass.  This works and
            # is valid, but results in ActionSchema being duplicated many times...
            # action_schema = build_action_schema(action_output, action_input)
        else:
            action_schema = ActionSchema

        d = self.spec_for_interaction(action)

        # Add in Action spec
        d = merge(
            d,
            {
                "post": {
                    "requestBody": {
                        "content": {
                            action.content_type: (
                                {"schema": action_input} if action_input else {}
                            )
                        }
                    },
                    "responses": {
                        # Responses like images must be added as
                        # 200 responses with cls.responses = {200: {...}}
                        200: {
                            "description": "Action completed immediately",
                            # Allow customising 200 (immediate response) content type?
                            # TODO: I'm not convinced it's still possible to customise this.
                            "content": {"application/json": {"schema": action_schema}},
                        },
                        201: {
                            "description": "Action started",
                            # Our POST 201 MUST be application/json
                            "content": {"application/json": {"schema": action_schema}},
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
                                    {
                                        "schema": {
                                            "type": "array",
                                            "items": action_schema,
                                        }
                                    }
                                )
                            },
                        }
                    },
                },
            },
        )
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

    # pylint: disable=signature-differs
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
