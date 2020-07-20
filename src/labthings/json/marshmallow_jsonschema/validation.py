from marshmallow import fields

from .exceptions import UnsupportedValueError


def handle_length(schema, field, validator, parent_schema):
    """Adds validation logic for ``marshmallow.validate.Length``, setting the
    values appropriately for ``fields.List``, ``fields.Nested``, and
    ``fields.String``.

    :param schema: The original JSON schema we generated. This is what we
            want to post-process.
    :type schema: dict
    :param field: The field that generated the original schema and
            who this post-processor belongs to.
    :type field: fields.Field
    :param validator: The validator attached to the
            passed in field.
    :type validator: marshmallow.validate.Length
    :param parent_schema: The Schema instance that the field
            belongs to.
    :type parent_schema: marshmallow.Schema
    :returns: A, possibly, new JSON Schema that has been post processed and
            altered.
    :rtype: dict
    :raises UnsupportedValueError: Raised if the `field` is something other than
            `fields.List`, `fields.Nested`, or `fields.String`

    """
    if isinstance(field, fields.String):
        minKey = "minLength"
        maxKey = "maxLength"
    elif isinstance(field, (fields.List, fields.Nested)):
        minKey = "minItems"
        maxKey = "maxItems"
    else:
        raise UnsupportedValueError(
            "In order to set the Length validator for JSON "
            "schema, the field must be either a List, Nested or a String"
        )

    if validator.min:
        schema[minKey] = validator.min

    if validator.max:
        schema[maxKey] = validator.max

    if validator.equal:
        schema[minKey] = validator.equal
        schema[maxKey] = validator.equal

    return schema


def handle_one_of(schema, field, validator, parent_schema):
    """Adds the validation logic for ``marshmallow.validate.OneOf`` by setting
    the JSONSchema `enum` property to the allowed choices in the validator.

    :param schema: The original JSON schema we generated. This is what we
            want to post-process.
    :type schema: dict
    :param field: The field that generated the original schema and
            who this post-processor belongs to.
    :type field: fields.Field
    :param validator: The validator attached to the
            passed in field.
    :type validator: marshmallow.validate.OneOf
    :param parent_schema: The Schema instance that the field
            belongs to.
    :type parent_schema: marshmallow.Schema
    :returns: New JSON Schema that has been post processed and
            altered.
    :rtype: dict

    """
    schema["enum"] = list(validator.choices)
    schema["enumNames"] = list(validator.labels)

    return schema


def handle_range(schema, field, validator, parent_schema):
    """Adds validation logic for ``marshmallow.validate.Range``, setting the
    values appropriately ``fields.Number`` and it's subclasses.

    :param schema: The original JSON schema we generated. This is what we
            want to post-process.
    :type schema: dict
    :param field: The field that generated the original schema and
            who this post-processor belongs to.
    :type field: fields.Field
    :param validator: The validator attached to the
            passed in field.
    :type validator: marshmallow.validate.Range
    :param parent_schema: The Schema instance that the field
            belongs to.
    :type parent_schema: marshmallow.Schema
    :returns: New JSON Schema that has been post processed and
            altered.
    :rtype: dict
    :raises UnsupportedValueError: Raised if the `field` is not an instance of
            `fields.Number`.

    """
    if not isinstance(field, fields.Number):
        raise UnsupportedValueError(
            "'Range' validator for non-number fields is not supported"
        )

    if validator.min is not None:
        # marshmallow 2 includes minimum by default
        # marshmallow 3 supports "min_inclusive"
        min_inclusive = getattr(validator, "min_inclusive", True)
        if min_inclusive:
            schema["minimum"] = validator.min
        else:
            schema["exclusiveMinimum"] = validator.min

    if validator.max is not None:
        # marshmallow 2 includes maximum by default
        # marshmallow 3 supports "max_inclusive"
        max_inclusive = getattr(validator, "max_inclusive", True)
        if max_inclusive:
            schema["maximum"] = validator.max
        else:
            schema["exclusiveMaximum"] = validator.max
    return schema


def handle_regexp(schema, field, validator, parent_schema):
    """Adds validation logic for ``marshmallow.validate.Regexp``, setting the
    values appropriately ``fields.String`` and it's subclasses.

    :param schema: The original JSON schema we generated. This is what we
            want to post-process.
    :type schema: dict
    :param field: The field that generated the original schema and
            who this post-processor belongs to.
    :type field: fields.Field
    :param validator: The validator attached to the
            passed in field.
    :type validator: marshmallow.validate.Regexp
    :param parent_schema: The Schema instance that the field
            belongs to.
    :type parent_schema: marshmallow.Schema
    :returns: New JSON Schema that has been post processed and
            altered.
    :rtype: dict
    :raises UnsupportedValueError: Raised if the `field` is not an instance of
            `fields.String`.

    """
    if not isinstance(field, fields.String):
        raise UnsupportedValueError(
            "'Regexp' validator for non-string fields is not supported"
        )

    schema["pattern"] = validator.regex.pattern

    return schema
