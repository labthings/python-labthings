from geventwebsocket.handler import WebSocketHandler
import gevent
import socket
import logging
import sys
import os
import signal
from werkzeug.debug import DebuggedApplication

from zeroconf import IPVersion, ServiceInfo, Zeroconf, get_all_addresses

from ..find import current_labthing


class Server:
    def __init__(self, app):
        self.app = app
        # Find LabThing attached to app
        self.labthing = current_labthing(app)

    def run(
        self,
        host="0.0.0.0",
        port=5000,
        log=None,
        debug=False,
        stop_timeout=1,
        zeroconf=True,
    ):
        # Type checks
        port = int(port)
        host = str(host)

        # Unmodified version of app
        app_to_run = self.app

        # Handle zeroconf
        zeroconf_server = None
        if zeroconf and self.labthing:
            service_info = ServiceInfo(
                "_labthings._tcp.local.",
                f"{self.labthing.title}._labthings._tcp.local.",
                port=port,
                properties={
                    "path": self.labthing.url_prefix,
                    "title": self.labthing.title,
                    "description": self.labthing.description,
                    "types": ";".join(self.labthing.types),
                },
                addresses=set(
                    [
                        socket.inet_aton(i)
                        for i in get_all_addresses()
                        if i not in ("127.0.0.1", "0.0.0.0")
                    ]
                ),
            )
            zeroconf_server = Zeroconf(ip_version=IPVersion.V4Only)
            zeroconf_server.register_service(service_info)

        # Handle logging
        if not log:
            log = logging.getLogger()

        # Handle debug mode
        if debug:
            log.setLevel(logging.DEBUG)
            app_to_run = DebuggedApplication(self.app)
            logging.getLogger("zeroconf").setLevel(logging.DEBUG)

        # Slightly more useful logger output
        friendlyhost = "localhost" if host == "0.0.0.0" else host
        logging.info("Starting LabThings WSGI Server")
        logging.info(f"Debug mode: {debug}")
        logging.info(f"Running on http://{friendlyhost}:{port} (Press CTRL+C to quit)")

        # Create WSGIServer
        wsgi_server = gevent.pywsgi.WSGIServer(
            (host, port), app_to_run, handler_class=WebSocketHandler, log=log
        )

        def stop():
            # Unregister zeroconf service
            if zeroconf_server:
                zeroconf_server.unregister_service(service_info)
                zeroconf_server.close()
            # Stop WSGI server with timeout
            wsgi_server.stop(timeout=stop_timeout)

        # Serve
        gevent.signal(signal.SIGTERM, stop)

        try:
            wsgi_server.serve_forever()
        except (KeyboardInterrupt, SystemExit):
            logging.warning("Terminating by KeyboardInterrupt or SystemExit")
            stop()
