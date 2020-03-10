from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
import logging
import sys
import os
from werkzeug.debug import DebuggedApplication


class Server:
    def __init__(self, app):
        self.app = app

    def run(self, host="0.0.0.0", port=5000, log=None, debug=False):
        # Type checks
        port = int(port)
        host = str(host)

        # Unmodified version of app
        app_to_run = self.app

        # Handle logging
        if not log:
            log = logging.getLogger()

        # Handle debug mode
        if debug:
            log.setLevel(logging.DEBUG)
            app_to_run = DebuggedApplication(self.app)

        friendlyhost = "localhost" if host == "0.0.0.0" else host
        logging.info("Starting LabThings WSGI Server")
        logging.info(f"Debug mode: {debug}")
        logging.info(f"Running on http://{friendlyhost}:{port} (Press CTRL+C to quit)")

        # Create WSGIServer
        wsgi_server = pywsgi.WSGIServer(
            (host, port), app_to_run, handler_class=WebSocketHandler, log=log
        )

        # Serve
        try:
            wsgi_server.serve_forever()
        except KeyboardInterrupt:
            logging.warning("Terminating by KeyboardInterrupt")
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
