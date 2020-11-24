from logging import StreamHandler


class LabThingLogger(StreamHandler):
    """ """

    def __init__(self, labthing, *args, ignore_werkzeug=True, **kwargs):
        StreamHandler.__init__(self, *args, **kwargs)
        self.labthing = labthing
        self.ignore_werkzeug = ignore_werkzeug

    def emit(self, record):
        if self.ignore_werkzeug and record.name == "werkzeug":
            return
        else:
            self.labthing.emit("logging", record)
