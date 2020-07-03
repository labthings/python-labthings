from marshmallow import Schema, fields

# from marshmallow_jsonschema import JSONSchema

from labthings.json.schemas import schema_to_json

from labthings.schema import FieldSchema


class UserSchema(Schema):
    username = fields.String()
    age = fields.Integer()
    birthday = fields.Date()


user_schema = UserSchema()

# print(json_schema.dump(s))
# print(json_schema.get_properties(s))
# print("")
# print(json_schema.dump(s))
# required = json_schema.get_required(s)
# print(required if required else None)

d = {
    "string": fields.String(required=True),
    "number": fields.Int(
        title="Foo", description="A number", missing=5, default=5, minimum=0
    ),
    "sub": {"string2": fields.String(), "number2": fields.Int()},
    "nested": fields.Nested(user_schema),
}
print(schema_to_json(d))
