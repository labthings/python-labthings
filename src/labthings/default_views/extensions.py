"""Top-level representation of attached and enabled Extensions"""
from ..find import registered_extensions
from ..schema import ExtensionSchema
from ..views import View


class ExtensionList(View):
    """List and basic documentation for all enabled Extensions"""

    tags = ["extensions"]

    def get(self):
        """List enabled extensions.

        Returns a list of Extension representations, including basic documentation.
        Describes server methods, web views, and other relevant Lab Things metadata.
        ---
        description: Extensions list
        summary: Extensions list
        responses:
            200:
                content:
                    application/json:
                        schema: ExtensionSchema
        """
        return ExtensionSchema(many=True).dump(registered_extensions().values() or [])
