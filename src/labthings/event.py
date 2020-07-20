import datetime


class Event:
    """ """
    def __init__(self, name, schema=None):
        self.name = name
        self.schema = schema

        self.events = []  # TODO: Make rotating

    def emit(self, data):
        """

        :param data: 

        """
        response = {
            "messageType": "event",
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "data": {self.name: data},
        }  # TODO: Format data with schema
        self.events.append(response)
        return response


class PropertyStatusEvent:
    """ """
    def __init__(self, property_name, schema=None):
        self.name = property_name

    def emit(self, data):
        """

        :param data: 

        """
        response = {
            "messageType": "propertyStatus",
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "data": {self.name: data},
        }
        return response


class ActionStatusEvent:
    """ """
    def __init__(self, action_name, schema=None):
        self.name = action_name

    def emit(self, data):
        """

        :param data: 

        """
        response = {
            "messageType": "actionStatus",
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "data": {self.name: data},
        }
        return response
