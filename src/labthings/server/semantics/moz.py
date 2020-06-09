from .. import decorators
from .. import fields

# BASIC PROPERTIES
class Property:
    def __init__(self, schema):
        self.schema = schema

    def __call__(self, viewcls):
        # Use the class name as the semantic type
        viewcls = decorators.Semtype(self.__class__.__name__)(viewcls)
        viewcls = decorators.PropertySchema(self.schema)(viewcls)
        return viewcls


class BooleanProperty(Property):
    """https://iot.mozilla.org/schemas/#BooleanProperty"""

    def __init__(self, **kwargs):
        schema = fields.Bool(required=True, **kwargs)
        Property.__init__(self, schema)


class LevelProperty(Property):
    """https://iot.mozilla.org/schemas/#LevelProperty"""

    def __init__(self, minimum, maximum, **kwargs):
        schema = fields.Int(required=True, minimum=minimum, maximum=maximum, **kwargs,)

        Property.__init__(self, schema)


# INHERITED PROPERTIES


class BrightnessProperty(LevelProperty):
    """https://iot.mozilla.org/schemas/#BrightnessProperty"""

    def __init__(self, **kwargs):
        LevelProperty.__init__(self, 0, 100, unit="percent", **kwargs)


class OnOffProperty(BooleanProperty):
    """https://iot.mozilla.org/schemas/#OnOffProperty"""

    def __init__(self, **kwargs):
        BooleanProperty.__init__(self, **kwargs)
