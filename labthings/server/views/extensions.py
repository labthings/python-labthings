"""Top-level representation of attached and enabled Extensions"""
from ..view import View
from ..find import registered_extensions
from ..schema import ExtensionSchema
from ..decorators import marshal_with


class ExtensionList(View):
    """List and basic documentation for all enabled Extensions"""

    @marshal_with(ExtensionSchema(many=True))
    def get(self):
        """
        List enabled extensions.

        Returns a list of Extension representations, including basic documentation.
        Describes server methods, web views, and other relevant Lab Things metadata.
        """
        return registered_extensions().values()
