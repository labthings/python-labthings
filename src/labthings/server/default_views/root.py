from ..find import current_labthing
from ..view import View


class RootView(View):
    def get(self):
        return current_labthing().thing_description.to_dict()
