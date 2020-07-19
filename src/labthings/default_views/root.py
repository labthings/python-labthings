from ..find import current_thing
from ..views import View


class RootView(View):
    """W3C Thing Description"""

    def get(self):
        return current_thing.thing_description.to_dict()
