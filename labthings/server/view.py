from flask.views import MethodView


class View(MethodView):
    """
    A LabThing Resource class should make use of functions get(), put(), post(), and delete() 
    corresponding to HTTP methods.

    These functions will allow for automated documentation generation
    """

    methods = ["get", "post", "put", "delete"]
    endpoint = None

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def doc(self):
        docs = {"operations": {}}
        if hasattr(self, "__apispec__"):
            docs.update(self.__apispec__)

        for meth in View.methods:
            if hasattr(self, meth) and hasattr(getattr(self, meth), "__apispec__"):
                docs["operations"][meth] = {}
                docs["operations"][meth] = getattr(self, meth).__apispec__
        return docs
