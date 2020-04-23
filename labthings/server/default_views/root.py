from ..find import current_labthing
from ..view import View


class RootView(View):
    @staticmethod
    def get():
        return current_labthing().thing_description.to_dict()
