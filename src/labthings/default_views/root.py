from ..find import current_labthing
from ..views import View


class RootView(View):
    """W3C Thing Description"""

    def get(self):
        """Thing Description
        ---
        description: Thing Description
        summary: Thing Description
        """
        return current_labthing().thing_description.to_dict()

    get.summary = "Thing Description"
    get.description = (
        "A W3C compliant Thing Description is a JSON representation\n"
        "of the API, including links to different endpoints.\n"
        "You can browse it directly (e.g. in Firefox), though for \n"
        "interactive API documentation you should try the swagger-ui \n"
        "docs, at `docs/swagger-ui/`"
    )
    get.responses = {
        "200": {
            "description": "W3C Thing Description",
            "content": {"application/json":{}},
        }
    }