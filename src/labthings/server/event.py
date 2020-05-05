import datetime


class Event:
    # Some event types are formatted slightly differently
    magic_types = {"propertyStatus", "actionStatus"}

    def __init__(self, name, schema=None):
        self.name = name
        self.schema = schema

        self.events = []  # TODO: Make rotating

    def emit(self, data):
        response = {
            "messageType": self.name if self.name in Event.magic_types else "event",
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "data": data if self.name in Event.magic_types else {self.name: data},
        }  # TODO: Format data with schema
        self.events.append(response)
        return response
