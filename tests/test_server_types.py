from labthings.server import types


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


def test_data_dict_to_schema():
    from labthings.server import fields
    from fractions import Fraction
    from marshmallow import Schema

    d = {
        "val1": Fraction(5, 2),
        "map1": {
            "subval1": "Hello",
            "subval2": False,
        },
        "val2": 5,
        "val3": [1, 2, 3, 4],
        "val4": range(1, 5),
    }

    gen_schema_dict = types.data_dict_to_schema(d)
    expected_schema_dict = {
        "val1": fields.Float(),
        "map1": {
            "subval1": fields.String(),
            "subval2": fields.Boolean(),
        },
        "val2": fields.Integer(),
        "val3": fields.List(fields.Int()),
        "val4": fields.List(fields.Int()),
    }

    gen_schema = Schema.from_dict(gen_schema_dict)()
    expected_schema = Schema.from_dict(expected_schema_dict)()

    assert gen_schema.dump(d) == expected_schema.dump(d)