from ..sockets import SocketSubscriber
from ..find import current_thing

import logging


STATIC_SOCKET_RESPONSES = {"__unittest": "__unittest_response"}


def socket_handler(ws):
    # Create a socket subscriber
    wssub = SocketSubscriber(ws)
    current_thing.subscribers.add(wssub)
    logging.info(f"Added subscriber {wssub}")
    # Start the socket connection handler loop
    while not ws.closed:
        message = ws.receive()
        if message is None:
            break
        response = process_socket_message(message)
        if response:
            ws.send(response)
    # Remove the subscriber once the loop returns
    current_thing.subscribers.remove(wssub)
    logging.info(f"Removed subscriber {wssub}")


def process_socket_message(message: str):
    if message:
        if message in STATIC_SOCKET_RESPONSES:
            return STATIC_SOCKET_RESPONSES.get(message)
        else:
            return message.upper()
    else:
        return None
