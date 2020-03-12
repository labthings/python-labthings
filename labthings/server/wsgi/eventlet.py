import eventlet.wsgi
import eventlet
import logging
import sys
import os
import signal
from werkzeug.debug import DebuggedApplication


class Server:
    def __init__(self, app):
        self.app = app

    def run(self, host="0.0.0.0", port=5000, log=None, debug=False, stop_timeout=1):
        # Type checks
        port = int(port)
        host = str(host)

        # Unmodified version of app
        app_to_run = self.app

        # Handle logging
        if not log:
            log = logging.getLogger()

        # Handle debug mode
        # if debug:
        #    log.setLevel(logging.DEBUG)
        #    app_to_run = DebuggedApplication(self.app)

        friendlyhost = "localhost" if host == "0.0.0.0" else host
        logging.info("Starting LabThings WSGI Server")
        logging.info(f"Debug mode: {debug}")
        logging.info(f"Running on http://{friendlyhost}:{port} (Press CTRL+C to quit)")

        # Create WSGIServer
        addresses = eventlet.green.socket.getaddrinfo(host, port)
        eventlet_socket = eventlet.listen(addresses[0][4], addresses[0][0])

        try:
            eventlet.wsgi.server(eventlet_socket, app_to_run)
        except (KeyboardInterrupt, SystemExit):
            logging.warning("Terminating by KeyboardInterrupt or SystemExit")
