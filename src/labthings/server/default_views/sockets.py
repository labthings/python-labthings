from ..sockets import SocketSubscriber, socket_handler_loop
from ..find import current_labthing

import logging


def socket_handler(ws):
    # Create a socket subscriber
    wssub = SocketSubscriber(ws)
    current_labthing().subscribers.add(wssub)
    logging.info(f"Added subscriber {wssub}")
    # Start the socket connection handler loop
    socket_handler_loop(ws)
    # Remove the subscriber once the loop returns
    current_labthing().subscribers.remove(wssub)
    logging.info(f"Removed subscriber {wssub}")
