from .. import decorators
from .. import fields


class Semantic:
    pass


# BASIC PROPERTIES
class Property(Semantic):
    def __init__(self, schema):
        self.schema = schema

    def __call__(self, viewcls):
        # Use the class name as the semantic type
        viewcls = decorators.Semtype(self.__class__.__name__)(viewcls)
        viewcls = decorators.PropertySchema(self.schema)(viewcls)
        return viewcls
