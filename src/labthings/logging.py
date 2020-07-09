from .find import current_thing

from logging import StreamHandler


class LabThingLogger(StreamHandler):
    def __init__(self, *args, **kwargs):
        StreamHandler.__init__(self, *args, **kwargs)

    def emit(self, record):
        log_event = self.rest_format_record(record)

        # Broadcast to subscribers
        if current_thing:
            current_thing.emit("logging", log_event)

    def rest_format_record(self, record):
        return {"message": str(record.msg), "level": record.levelname.lower()}
