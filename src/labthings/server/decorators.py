from http import HTTPStatus

from .view import View

from labthings.core.utilities import merge


# Useful externals to have included here
from marshmallow import pre_dump, pre_load

__all__ = [
    "pre_dump",
    "pre_load",
    "Safe",
    "safe",
    "Idempotent",
    "idempotent",
    "PropertySchema",
    "Doc",
    "doc",
    "Tag",
    "tag",
    "doc_response",
]


def Safe(viewcls: View):
    """Decorator to tag a view or function as being safe

    Args:
        viewcls (View): View class to tag as Safe

    Returns:
        View: View class with Safe spec tags
    """
    # Update Views API spec
    viewcls.safe = True
    return viewcls


safe = Safe


def Idempotent(viewcls: View):
    """Decorator to tag a view or function as being idempotent

    Args:
        viewcls (View): View class to tag as idempotent

    Returns:
        View: View class with idempotent spec tags
    """
    # Update Views API spec
    viewcls.idempotent = True
    return viewcls


idempotent = Idempotent


class PropertySchema:
    def __init__(self, schema):
        """
        :param schema: a dict of whose keys will make up the final
                        serialized response output
        """
        self.schema = schema

    def __call__(self, viewcls: View):
        viewcls.schema = self.schema
        return viewcls


class Doc:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, viewcls: View):
        # Pass params to call function attribute for external access
        viewcls.docs.update(self.kwargs)
        return viewcls


doc = Doc


class Tag:
    def __init__(self, tags):
        if type(tags) is str:
            tags = [tags]
        self.tags = tags

    def __call__(self, viewcls: View):
        # Pass params to call function attribute for external access
        viewcls.tags.extend(self.tags)
        return viewcls


tag = Tag


class Semtype:
    def __init__(self, semtype: str):
        self.semtype = semtype

    def __call__(self, viewcls: View):
        # Pass params to call function attribute for external access
        viewcls.semtype = self.semtype
        return viewcls


semtype = Semtype
