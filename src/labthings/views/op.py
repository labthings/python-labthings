import copy


class readproperty:
    def __init__(self, fn):
        self.fn = fn

    def __set_name__(self, owner, name):
        if hasattr(owner, "_opmap"):
            owner._opmap = copy.copy(owner._opmap)
            owner._opmap.update({"readproperty": name})

        # then replace ourself with the original method
        setattr(owner, name, self.fn)


class writeproperty:
    def __init__(self, fn):
        self.fn = fn

    def __set_name__(self, owner, name):
        if hasattr(owner, "_opmap"):
            owner._opmap = copy.copy(owner._opmap)
            owner._opmap.update({"writeproperty": name})

        # then replace ourself with the original method
        setattr(owner, name, self.fn)


class observeproperty:
    def __init__(self, fn):
        self.fn = fn

    def __set_name__(self, owner, name):
        if hasattr(owner, "_opmap"):
            owner._opmap = copy.copy(owner._opmap)
            owner._opmap.update({"observeproperty": name})

        # then replace ourself with the original method
        setattr(owner, name, self.fn)
