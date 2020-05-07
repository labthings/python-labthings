from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from ...core.utilities import merge, get_docstring, get_summary

from ..fields import Field
from marshmallow import Schema as BaseSchema

from collections.abc import Mapping


def compile_view_spec(view):
    """Compile a complete API Spec of a View and its HTTP methods

    Arguments:
        view {View} -- LabThings View class

    Returns:
        [dict] -- Compiled API Spec
    """
    # TODO: Build Action 201 response spec
    spec = get_spec(view)

    spec["description"] = spec.get("description") or get_docstring(view)
    spec["summary"] = spec.get("summary") or get_summary(view) or spec["description"]
    spec["tags"] = spec.get("tags", set())

    spec["_operations"] = {}
    for operation in ("get", "post", "put", "delete"):
        meth = getattr(view, operation, None)
        if meth:
            meth_spec = get_spec(meth)

            meth_spec["description"] = (
                meth_spec.get("description")
                or get_docstring(meth)
                or spec["description"]
            )

            meth_spec["summary"] = (
                meth_spec.get("summary") or get_summary(meth) or spec["summary"]
            )

            meth_spec["tags"] = meth_spec.get("tags", set())
            meth_spec["tags"] = meth_spec["tags"].union(spec["tags"])

            spec["_operations"][operation] = meth_spec
    return spec


def update_spec(obj, spec: dict):
    """Add API spec data to an object

    Args:
        obj: Python object
        spec (dict): Dictionary of API spec data to add
    """
    # obj.__apispec__ = obj.__dict__.get("__apispec__", {})
    obj.__apispec__ = getattr(obj, "__apispec__", {})
    obj.__apispec__ = merge(obj.__apispec__, spec)
    return obj.__apispec__ or {}


def tag_spec(obj, tags, add_group: bool = True):
    obj.__apispec__ = obj.__dict__.get("__apispec__", {})

    if "tags" not in obj.__apispec__:
        obj.__apispec__["tags"] = set()

    if isinstance(tags, set) or isinstance(tags, list):
        if not all(isinstance(e, str) for e in tags):
            raise TypeError("All tags must be strings")
        obj.__apispec__["tags"] = obj.__apispec__["tags"].union(tags)
    elif isinstance(tags, str):
        obj.__apispec__["tags"].add(tags)
    else:
        raise TypeError("All tags must be strings")


def get_spec(obj):
    """
    Get the __apispec__ dictionary, created by LabThings decorators,
    for a particular Python object

    Args:
        obj: Python object

    Returns:
        dict: API spec dictionary. Returns empty dictionary if no spec is found.
    """
    if not obj:
        return {}
    obj.__apispec__ = getattr(obj, "__apispec__", {})
    return obj.__apispec__ or {}


def get_topmost_spec_attr(view, spec_key: str):
    """
    Get the __apispec__ value corresponding to spec_key, from first the root view,
    falling back to GET, POST, and PUT in that descending order of priority

    Args:
        obj: Python object

    Returns:
        spec value corresponding to spec_key
    """
    spec = get_spec(view)
    value = spec.get(spec_key)

    if not value:
        for meth in ["get", "post", "put"]:
            spec = get_spec(getattr(view, meth, None))
            value = spec.get(spec_key)
            if value:
                break
    return value


def convert_schema(schema, spec: APISpec):
    """
    Ensure that a given schema is either a real Marshmallow schema,
    or is a dictionary describing the schema inline.

    Marshmallow schemas are left as they are so that the APISpec module
    can add them to the "schemas" list in our APISpec documentation.
    """
    # Don't process Nones
    if not schema:
        return schema

    # Expand/convert actual schema data
    if isinstance(schema, BaseSchema):
        return schema
    elif isinstance(schema, Mapping):
        return map_to_properties(schema, spec)
    elif isinstance(schema, Field):
        return field_to_property(schema, spec)
    else:
        raise TypeError(
            f"Unsupported schema type {schema}. "
            "Ensure schema is a Schema class, or dictionary of Field objects"
        )


def map_to_properties(schema, spec: APISpec):
    """
    Recursively convert any dictionary-like map of Marshmallow fields
    into a dictionary describing it's JSON schema
    """
    marshmallow_plugin = next(
        plugin for plugin in spec.plugins if isinstance(plugin, MarshmallowPlugin)
    )
    converter = marshmallow_plugin.converter

    d = {}
    for k, v in schema.items():
        if isinstance(v, Field):
            d[k] = converter.field2property(v)
        elif isinstance(v, Mapping):
            d[k] = map_to_properties(v, spec)
        else:
            d[k] = v

    return {"type": "object", "properties": d}


def field_to_property(field, spec: APISpec):
    """Convert a single Marshmallow field into a JSON schema of that field"""
    marshmallow_plugin = next(
        plugin for plugin in spec.plugins if isinstance(plugin, MarshmallowPlugin)
    )
    converter = marshmallow_plugin.converter

    return converter.field2property(field)


def schema_to_json(schema, spec: APISpec):
    """
    Convert any Marshmallow schema stright to a fully expanded JSON schema.
    This should not be used when generating APISpec documentation,
    otherwise schemas wont be listed in the "schemas" list.
    This is used, for example, in the Thing Description.
    """

    if isinstance(schema, BaseSchema):
        marshmallow_plugin = next(
            plugin for plugin in spec.plugins if isinstance(plugin, MarshmallowPlugin)
        )
        converter = marshmallow_plugin.converter

        schema = converter.schema2jsonschema(schema)

    schema = recursive_expand_refs(schema, spec)

    return schema


def recursive_expand_refs(schema_dict, spec: APISpec):
    """
    Traverse `schema_dict` expanding out all schema $ref values where possible.

    Used when generating Thing Descriptions, so each attribute contains full schemas.
    """
    if isinstance(schema_dict, Mapping):
        if "$ref" in schema_dict:
            schema_dict = expand_refs(schema_dict, spec)

        for k, v in schema_dict.items():
            if isinstance(v, Mapping):
                schema_dict[k] = recursive_expand_refs(v, spec)

    return schema_dict


def expand_refs(schema_dict, spec: APISpec):
    """
    Expand out all schema $ref values where possible.

    Uses the $ref value to look up a particular schema in spec schemas
    """
    if "$ref" not in schema_dict:
        return schema_dict

    name = schema_dict.get("$ref").split("/")[-1]

    # Get the list of all schemas registered with APISpec
    spec_schemas = spec.to_dict().get("components", {}).get("schemas", {})

    if name in spec_schemas:
        schema_dict.update(spec_schemas.get(name))
        del schema_dict["$ref"]

    return schema_dict
