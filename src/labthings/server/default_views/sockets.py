from ..sockets import SocketSubscriber
from ..find import current_labthing

import gevent
import logging


def socket_handler(ws):
    # Create a socket subscriber
    wssub = SocketSubscriber(ws)
    current_labthing().subscribers.add(wssub)
    logging.info(f"Added subscriber {wssub}")
    # Start the socket connection handler loop
    while not ws.closed:
        message = ws.receive()
        if message is None:
            break
        response = process_socket_message(message)
        if response:
            ws.send(response)
        gevent.sleep(0.1)
    # Remove the subscriber once the loop returns
    current_labthing().subscribers.remove(wssub)
    logging.info(f"Removed subscriber {wssub}")


def process_socket_message(message: str):
    if message:
        return None
    else:
        return None
