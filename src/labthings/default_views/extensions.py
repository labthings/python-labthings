"""Top-level representation of attached and enabled Extensions"""
from ..find import registered_extensions
from ..schema import ExtensionSchema
from ..views import View, described_operation


class ExtensionList(View):
    """List and basic documentation for all enabled Extensions"""

    tags = ["extensions"]

    @described_operation
    def get(self):
        """List enabled extensions.

        Returns a list of Extension representations, including basic documentation.
        Describes server methods, web views, and other relevant Lab Things metadata.
        """
        return ExtensionSchema(many=True).dump(registered_extensions().values() or [])

    get.responses = {
        "200": {
            "description": "A list of available extensions and their properties",
            "content": {"application/json": {"schema": ExtensionSchema}},
        }
    }
