from .find import current_labthing

from logging import StreamHandler
import datetime


class LabThingLogger(StreamHandler):
    def __init__(self, *args, **kwargs):
        StreamHandler.__init__(self, *args, **kwargs)

    def emit(self, record):
        log_event = self.rest_format_record(record)

        # Broadcast to subscribers
        if current_labthing():
            current_labthing().emit(log_event)

    def rest_format_record(self, record):
        data = {
            "data": str(record.msg),
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }
        level_string = record.levelname.lower()

        return {level_string: data}
