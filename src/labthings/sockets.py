from .representations import encode_json


class SocketSubscriber:
    """ """
    def __init__(self, ws):
        self.ws = ws

    def emit(self, event: dict):
        """

        :param event: dict: 

        """
        response = encode_json(event)
        # TODO: Logic surrounding if this subscriber is subscribed to the requested event type
        self.ws.send(response)
