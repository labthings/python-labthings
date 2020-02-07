from labthings.server import types, fields
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


def test_make_primative():
    from fractions import Fraction

    assert types.make_primative(Fraction(5, 2)) == 2.5


def test_value_to_field():
    from labthings.server import fields

    # Test arrays of data
    d1 = [1, 2, 3]
    gen_field = types.value_to_field(d1)
    expected_field = fields.List(fields.Int())

    assert gen_field._serialize(d1, None, None) == expected_field._serialize(
        d1, None, None
    )

    # Test single values
    d2 = "String"
    gen_field_2 = types.value_to_field(d2)
    expected_field_2 = fields.String(example="String")

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
