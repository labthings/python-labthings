from ..find import current_labthing
from ..views import View


class RootView(View):
    """W3C Thing Description"""

    def get(self):
        """ """
        return current_labthing().thing_description.to_dict()
