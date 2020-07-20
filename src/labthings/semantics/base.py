from .. import fields


class Semantic:
    """ """
    def __call__(self, viewcls):
        # Use the class name as the semantic type
        viewcls.semtype = self.__class__.__name__
        return viewcls


# BASIC PROPERTIES
class Property(Semantic):
    """ """
    def __init__(self, schema):
        self.schema = schema

    def __call__(self, viewcls):
        # Use the class name as the semantic type
        viewcls.semtype = self.__class__.__name__
        viewcls.schema = self.schema
        return viewcls
