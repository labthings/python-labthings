import copy


class _opannotation:
    def __init__(self, fn):
        self.fn = fn

    def __set_name__(self, owner, name):
        if hasattr(owner, "_opmap"):
            owner._opmap = copy.copy(owner._opmap)
            owner._opmap.update({self.__class__.__name__: name})

        # then replace ourself with the original method
        setattr(owner, name, self.fn)


class readproperty(_opannotation):
    pass


class observeproperty(_opannotation):
    pass


class unobserveproperty(_opannotation):
    pass


class writeproperty(_opannotation):
    pass


class invokeaction(_opannotation):
    pass
