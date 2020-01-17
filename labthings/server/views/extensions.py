"""
Top-level representation of attached and enabled Extensions
"""
from ..view import View
from ..find import registered_extensions
from ..schema import ExtensionSchema
from ..decorators import marshal_with, ThingProperty


@ThingProperty
class ExtensionList(View):
    """
    List and basic documentation for all enabled Extensions
    """

    @marshal_with(ExtensionSchema(many=True))
    def get(self):
        """
        Return the current Extension forms

        Returns an array of present Extension forms (describing Extension user interfaces.)
        Please note, this is *not* a list of all enabled Extensions, only those with associated
        user interface forms.

        A complete list of enabled Extensions can be found in the microscope state.

        """
        return registered_extensions().values()
