import pytest
from jsonschema import Draft7Validator

from labthings import fields
from labthings.json.marshmallow_jsonschema import JSONSchema, UnsupportedValueError
from labthings.schema import Schema, validate


class Address(Schema):
    id = fields.String(default="no-id")
    street = fields.String(required=True)
    number = fields.String(required=True)
    city = fields.String(required=True)
    floor = fields.Integer(validate=validate.Range(min=1, max=4))


class GithubProfile(Schema):
    uri = fields.String(required=True)


class UserSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    age = fields.Float()
    created = fields.DateTime()
    created_formatted = fields.DateTime(
        format="%Y-%m-%d", attribute="created", dump_only=True
    )
    created_iso = fields.DateTime(format="iso", attribute="created", dump_only=True)
    updated = fields.DateTime()
    species = fields.String(attribute="SPECIES")
    id = fields.String(default="no-id")
    homepage = fields.Url()
    email = fields.Email()
    balance = fields.Decimal()
    registered = fields.Boolean()
    hair_colors = fields.List(fields.Raw)
    sex_choices = fields.List(fields.Raw)
    finger_count = fields.Integer()
    uid = fields.UUID()
    time_registered = fields.Time()
    birthdate = fields.Date()
    since_created = fields.TimeDelta()
    sex = fields.Str(
        validate=validate.OneOf(
            choices=["male", "female", "non_binary", "other"],
            labels=["Male", "Female", "Non-binary/fluid", "Other"],
        )
    )
    various_data = fields.Dict()
    addresses = fields.Nested(
        Address, many=True, validate=validate.Length(min=1, max=3)
    )
    github = fields.Nested(GithubProfile)
    const = fields.String(validate=validate.Length(equal=50))
    bytestring = fields.Bytes()


def _validate_schema(schema):
    """
    raises jsonschema.exceptions.SchemaError
    """
    Draft7Validator.check_schema(schema)


def validate_and_dump(schema):
    json_schema = JSONSchema()
    data = json_schema.dump(schema)
    _validate_schema(data)
    return data


def test_dump_schema():
    schema = UserSchema()

    dumped = validate_and_dump(schema)

    assert len(schema.fields) > 1

    props = dumped["properties"]
    for field_name, field in schema.fields.items():
        assert field_name in props


def test_default():
    schema = UserSchema()

    dumped = validate_and_dump(schema)

    props = dumped["properties"]
    assert props["id"]["default"] == "no-id"


def test_metadata():
    """Metadata should be available in the field definition."""

    class TestSchema(Schema):
        myfield = fields.String(metadata={"foo": "Bar"})
        yourfield = fields.Integer(required=True, baz="waz")

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    props = dumped["properties"]
    assert props["myfield"]["foo"] == "Bar"
    assert props["yourfield"]["baz"] == "waz"
    assert "metadata" not in props["myfield"]
    assert "metadata" not in props["yourfield"]

    # repeat process to assert idempotency
    dumped = validate_and_dump(schema)

    props = dumped["properties"]
    assert props["myfield"]["foo"] == "Bar"
    assert props["yourfield"]["baz"] == "waz"


def test_descriptions():
    class TestSchema(Schema):
        myfield = fields.String(description="Brown Cow")
        yourfield = fields.Integer(required=True)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    props = dumped["properties"]
    assert props["myfield"]["description"] == "Brown Cow"


def test_nested_descriptions():
    class TestNestedSchema(Schema):
        myfield = fields.String(description="Brown Cow")
        yourfield = fields.Integer(required=True)

    class TestSchema(Schema):
        nested = fields.Nested(
            TestNestedSchema, metadata={"description": "Nested 1", "title": "Title1"}
        )
        yourfield_nested = fields.Integer(required=True)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["properties"]["nested"]["description"] == "Nested 1"
    assert dumped["properties"]["nested"]["title"] == "Title1"
    assert (
        dumped["properties"]["nested"]["properties"]["myfield"]["description"]
        == "Brown Cow"
    )


def test_nested_string_to_cls():
    class TestNamedNestedSchema(Schema):
        foo = fields.Integer(required=True)

    class TestSchema(Schema):
        foo2 = fields.Integer(required=True)
        nested = fields.Nested("TestNamedNestedSchema")

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    nested_dmp = dumped["properties"]["nested"]
    assert nested_dmp["type"] == "object"
    assert nested_dmp["properties"]["foo"]["format"] == "integer"


def test_list():
    class ListSchema(Schema):
        foo = fields.List(fields.String(), required=True)

    schema = ListSchema()
    dumped = validate_and_dump(schema)

    nested_json = dumped["properties"]["foo"]
    assert nested_json["type"] == "array"
    assert "items" in nested_json

    item_schema = nested_json["items"]
    assert item_schema["type"] == "string"


def test_list_nested():
    """Test that a list field will work with an inner nested field."""

    class InnerSchema(Schema):
        foo = fields.Integer(required=True)

    class ListSchema(Schema):
        bar = fields.List(fields.Nested(InnerSchema), required=True)

    schema = ListSchema()
    dumped = validate_and_dump(schema)

    nested_json = dumped["properties"]["bar"]

    assert nested_json["type"] == "array"
    assert "items" in nested_json

    item_schema = nested_json["items"]
    assert item_schema == {
        "required": ["foo"],
        "properties": {"foo": {"type": "number", "format": "integer"}},
        "type": "object",
    }


def test_function():
    """Function fields can be serialised if type is given."""

    class FnSchema(Schema):
        fn_str = fields.Function(
            lambda: "string", required=True, _jsonschema_type_mapping={"type": "string"}
        )
        fn_int = fields.Function(
            lambda: 123, required=True, _jsonschema_type_mapping={"type": "number"}
        )

    schema = FnSchema()

    dumped = validate_and_dump(schema)

    props = dumped["properties"]
    assert props["fn_int"]["type"] == "number"
    assert props["fn_str"]["type"] == "string"


def test_unknown_typed_field_throws_valueerror():
    class Invalid(fields.Field):
        def _serialize(self, value, attr, obj):
            return value

    class UserSchema(Schema):
        favourite_colour = Invalid()

    schema = UserSchema()
    json_schema = JSONSchema()

    with pytest.raises(UnsupportedValueError):
        validate_and_dump(json_schema.dump(schema))


def test_unknown_typed_field():
    class Colour(fields.Field):
        def _jsonschema_type_mapping(self):
            return {"type": "string"}

    class UserSchema(Schema):
        name = fields.String(required=True)
        favourite_colour = Colour()

    schema = UserSchema()

    dumped = validate_and_dump(schema)

    assert dumped["properties"]["favourite_colour"] == {"type": "string"}


def test_field_subclass():
    """JSON schema generation should not fail on sublcass marshmallow field."""

    class CustomField(fields.Field):
        pass

    class TestSchema(Schema):
        myfield = CustomField()

    schema = TestSchema()
    with pytest.raises(UnsupportedValueError):
        _ = validate_and_dump(schema)


def test_readonly():
    class TestSchema(Schema):
        id = fields.Integer(required=True)
        readonly_fld = fields.String(dump_only=True)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["properties"]["readonly_fld"] == {
        "type": "string",
        "readonly": True,
    }


def test_allow_none():
    """A field with allow_none set to True should have type null as additional."""

    class TestSchema(Schema):
        id = fields.Integer(required=True)
        readonly_fld = fields.String(allow_none=True)

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["properties"]["readonly_fld"] == {
        "type": ["string", "null"],
    }


def test_dumps_iterable_enums():
    mapping = {"a": 0, "b": 1, "c": 2}

    class TestSchema(Schema):
        foo = fields.Integer(
            validate=validate.OneOf(mapping.values(), labels=mapping.keys())
        )

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["properties"]["foo"] == {
        "enum": [v for v in mapping.values()],
        "enumNames": [k for k in mapping.keys()],
        "format": "integer",
        "type": "number",
    }


def test_required_excluded_when_empty():
    class TestSchema(Schema):
        optional_value = fields.String()

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert "required" not in dumped


def test_datetime_based():
    class TestSchema(Schema):
        f_date = fields.Date()
        f_datetime = fields.DateTime()
        f_time = fields.Time()

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["properties"]["f_date"] == {
        "format": "date",
        "type": "string",
    }

    assert dumped["properties"]["f_datetime"] == {
        "format": "date-time",
        "type": "string",
    }

    assert dumped["properties"]["f_time"] == {
        "format": "time",
        "type": "string",
    }


def test_sorting_properties():
    class TestSchema(Schema):
        class Meta:
            ordered = True

        d = fields.Str()
        c = fields.Str()
        a = fields.Str()

    # Should be sorting of fields
    schema = TestSchema()

    json_schema = JSONSchema()
    data = json_schema.dump(schema)

    sorted_keys = sorted(data["properties"].keys())
    properties_names = [k for k in sorted_keys]
    assert properties_names == ["a", "c", "d"]

    # Should be saving ordering of fields
    schema = TestSchema()

    json_schema = JSONSchema(props_ordered=True)
    data = json_schema.dump(schema)

    keys = data["properties"].keys()
    properties_names = [k for k in keys]

    assert properties_names == ["d", "c", "a"]


def test_validate_range():
    class TestSchema(Schema):
        foo = fields.Integer(
            validate=validate.Range(
                min=1, min_inclusive=False, max=3, max_inclusive=False
            )
        )
        bar = fields.Integer(validate=validate.Range(min=2, max=4))

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    props = dumped["properties"]
    assert props["foo"]["exclusiveMinimum"] == 1
    assert props["foo"]["exclusiveMaximum"] == 3
    assert props["bar"]["minimum"] == 2
    assert props["bar"]["maximum"] == 4


def test_range_no_min_or_max():
    class SchemaNoMin(Schema):
        foo = fields.Integer(validate=validate.Range(max=4))

    class SchemaNoMax(Schema):
        foo = fields.Integer(validate=validate.Range(min=0))

    schema1 = SchemaNoMin()
    schema2 = SchemaNoMax()

    dumped1 = validate_and_dump(schema1)
    dumped2 = validate_and_dump(schema2)
    assert dumped1["properties"]["foo"]["maximum"] == 4
    assert dumped2["properties"]["foo"]["minimum"] == 0


def test_range_non_number_error():
    class TestSchema(Schema):
        foo = fields.String(validate=validate.Range(max=4))

    schema = TestSchema()

    json_schema = JSONSchema()

    with pytest.raises(UnsupportedValueError):
        json_schema.dump(schema)


def test_regexp():
    ipv4_regex = (
        r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}"
        r"([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
    )

    class TestSchema(Schema):
        ip_address = fields.String(validate=validate.Regexp(ipv4_regex))

    schema = TestSchema()

    dumped = validate_and_dump(schema)

    assert dumped["properties"]["ip_address"] == {
        "type": "string",
        "pattern": ipv4_regex,
    }


def test_regexp_error():
    class TestSchema(Schema):
        test_regexp = fields.Int(validate=validate.Regexp(r"\d+"))

    schema = TestSchema()

    with pytest.raises(UnsupportedValueError):
        dumped = validate_and_dump(schema)
