from .. import fields


class Semantic:
    """ """

    def __call__(self, obj):
        # Use the class name as the semantic type
        obj.semtype = self.__class__.__name__
        return obj


# BASIC PROPERTIES
class Property(Semantic):
    """ """

    def __init__(self, schema):
        self.schema = schema

    def __call__(self, obj):
        # Use the class name as the semantic type
        obj.semtype = self.__class__.__name__
        obj.schema = self.schema
        return obj
