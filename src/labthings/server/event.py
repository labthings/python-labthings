import datetime


class Event:
    def __init__(self, name, schema=None):
        self.name = name
        self.schema = schema

        self.events = []  # TODO: Make rotating

    def emit(self, data):
        response = {
            "messageType": self.name,
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "data": data,
        }  # TODO: Format data with schema
        self.events.append(response)
        return response
