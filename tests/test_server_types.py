from labthings.server import types, fields
from labthings.server.types.registry import TypeRegistry
import pytest

from fractions import Fraction
from datetime import datetime
import uuid


@pytest.fixture
def types_dict():
    d = {
        "fraction": Fraction(5, 2),
        "map1": {"string": "Hello", "bool": False},
        "int": 5,
        "list_int": [1, 2, 3, 4],
        "range": range(1, 5),
        "datetime": datetime.today(),
        "uuid": uuid.uuid4(),
    }

    s = {
        "fraction": fields.Float(),
        "map1": {"string": fields.String(), "bool": fields.Boolean()},
        "int": fields.Integer(),
        "list_int": fields.List(fields.Int()),
        "range": fields.List(fields.Int()),
        "datetime": fields.DateTime(),
        "uuid": fields.UUID(),
    }

    return d, s


def test_make_primitive():
    import numpy

    generic_object = object()

    assert types.make_primitive(Fraction(5, 2)) == 2.5
    assert types.make_primitive(numpy.array([1, 2, 3])) == [1, 2, 3]
    assert types.make_primitive(numpy.int16(10)) == 10

    assert type(types.make_primitive(generic_object)) == str
    assert types.make_primitive(generic_object).startswith("<object object at ")

    assert types.make_primitive(10) == 10


def test_value_to_field():
    # Test arrays of data
    d1 = [1, 2, 3]
    gen_field = types.value_to_field(d1)
    expected_field = fields.List(fields.Int())

    # skipcq: PYL-W0212
    assert gen_field._serialize(d1, None, None) == expected_field._serialize(
        d1, None, None
    )

    # Test single values
    d2 = "String"
    gen_field_2 = types.value_to_field(d2)
    expected_field_2 = fields.String(example="String")

    # skipcq: PYL-W0212
    assert gen_field_2._serialize(d2, None, None) == expected_field_2._serialize(
        d2, None, None
    )


def test_data_dict_to_schema(types_dict):
    from marshmallow import Schema

    data, expected_schema_dict = types_dict
    gen_schema_dict = types.data_dict_to_schema(data)

    gen_schema = Schema.from_dict(gen_schema_dict)()
    expected_schema = Schema.from_dict(expected_schema_dict)()

    assert gen_schema.dump(data) == expected_schema.dump(data)


def test_function_signature_to_schema():
    from typing import List
    from marshmallow import Schema

    def test_func(
        positional: int, n: int = 10, optlist: List[int] = [1, 2, 3], untyped="untyped"
    ):
        pass

    gen_schema_dict = types.function_signature_to_schema(test_func)
    gen_schema = Schema.from_dict(gen_schema_dict)()

    expected_schema = Schema.from_dict(
        {
            "positional": fields.Int(),
            "n": fields.Int(default=10, example=10),
            "optlist": fields.List(fields.Int, default=[1, 2, 3], example=[1, 2, 3]),
            "untyped": fields.Field(default="untyped", example="untyped"),
        }
    )()

    data = {"positional": 10, "n": 50, "optlist": [4, 5, 6], "untyped": True}
    assert gen_schema.dump(data) == expected_schema.dump(data)


def test_type_registry():
    registry = TypeRegistry()

    assert registry.has(str) == True

    with pytest.raises(TypeError):
        registry.get(object)


def test_annotation_converter():
    from inspect import Parameter

    converter = types.AnnotationConverter()

    test_parameter = Parameter(
        "test", Parameter.KEYWORD_ONLY, annotation=int, default=1
    )
    test_parameter_field = converter.convert(test_parameter)
    assert isinstance(test_parameter_field, fields.Field)

    test_type = int
    test_type_field = converter.convert(test_type)
    assert isinstance(test_type_field, fields.Field)

    test_value = 5
    test_value_field = converter.convert(test_value)
    assert isinstance(test_value_field, fields.Field)
