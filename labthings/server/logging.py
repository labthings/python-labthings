from logging import StreamHandler
import datetime


class LabThingLogger(StreamHandler):
    def __init__(self, labthing):
        StreamHandler.__init__(self)
        self.labthing = labthing

    def emit(self, record):
        log_event = self.rest_format_record(record)

        # Broadcast to subscribers
        subscribers = getattr(self.labthing, "subscribers", [])
        for sub in subscribers:
            sub.event_notify(log_event)

    def rest_format_record(self, record):
        data = {
            "data": str(record.msg),
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }
        level_string = record.levelname.lower()

        return {level_string: data}
