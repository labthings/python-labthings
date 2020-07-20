import socket
import signal
import logging
import threading

from werkzeug.debug import DebuggedApplication
from zeroconf import IPVersion, ServiceInfo, Zeroconf, get_all_addresses
from flask_threaded_sockets import ThreadedWebsocketServer

from .find import current_labthing

sentinel = object()


class Server:
    """Combined WSGI+WebSocket+mDNS server.

    :param host: Host IP address. Defaults to 0.0.0.0.
    :type host: string
    :param port: Host port. Defaults to 7485.
    :type port: int
    :param debug: Enable server debug mode. Defaults to False.
    :type debug: bool
    :param zeroconf: Enable the zeroconf (mDNS) server. Defaults to True.
    :type zeroconf: bool
    """

    def __init__(
        self, app, host="0.0.0.0", port=7485, debug=False, zeroconf=True, **kwargs
    ):
        self.app = app
        # Find LabThing attached to app
        self.labthing = current_labthing(app)

        # Server properties
        self.host = host
        self.port = port
        self.debug = debug
        self.zeroconf = zeroconf

        # Servers
        self.wsgi_server = None
        self.zeroconf_server = None
        self.service_info = None
        self.service_infos = []

        # Events
        self.started = threading.Event()

    def _register_zeroconf(self):
        if self.labthing:
            # Get list of host addresses
            mdns_addresses = {
                socket.inet_aton(i)
                for i in get_all_addresses()
                if i not in ("127.0.0.1", "0.0.0.0")
            }
            # LabThing service
            self.service_infos.append(
                ServiceInfo(
                    "_labthing._tcp.local.",
                    f"{self.labthing.safe_title}._labthing._tcp.local.",
                    port=self.port,
                    properties={
                        "path": self.labthing.url_prefix,
                        "title": self.labthing.title,
                        "description": self.labthing.description,
                        "types": ";".join(self.labthing.types),
                    },
                    addresses=mdns_addresses,
                )
            )
            self.zeroconf_server = Zeroconf(ip_version=IPVersion.V4Only)
            for service in self.service_infos:
                self.zeroconf_server.register_service(service)

    def stop(self):
        """Stop the server and unregister mDNS records"""
        # Unregister zeroconf service
        if self.zeroconf_server:
            logging.info("Unregistering zeroconf services")
            for service in self.service_infos:
                self.zeroconf_server.unregister_service(service)
            self.zeroconf_server.close()
        # Stop WSGI server with timeout
        if self.wsgi_server:
            logging.info("Shutting down WSGI server")
            self.wsgi_server.stop(timeout=5)
        # Clear started event
        if self.started.is_set():
            self.started.clear()
        logging.info("Done")

    def start(self):
        """Start the server and register mDNS records"""
        # Unmodified version of app
        app_to_run = self.app
        # Handle zeroconf
        if self.zeroconf:
            self._register_zeroconf()

        # Handle debug mode
        if self.debug:
            app_to_run = DebuggedApplication(self.app)
            logging.getLogger("werkzeug").setLevel(logging.DEBUG)
            logging.getLogger("zeroconf").setLevel(logging.DEBUG)

        # Slightly more useful logger output
        friendlyhost = "localhost" if self.host == "0.0.0.0" else self.host
        print("Starting LabThings WSGI Server")
        print(f"Debug mode: {self.debug}")
        print(f"Running on http://{friendlyhost}:{self.port} (Press CTRL+C to quit)")

        # Create WSGIServer
        self.wsgi_server = ThreadedWebsocketServer(self.host, self.port, app_to_run)

        # Serve
        signal.signal(signal.SIGTERM, self.stop)

        # Set started event
        self.started.set()
        try:
            self.wsgi_server.serve_forever()
        except (KeyboardInterrupt, SystemExit):  # pragma: no cover
            logging.warning(
                "Terminating by KeyboardInterrupt or SystemExit"
            )  # pragma: no cover
            self.stop()  # pragma: no cover

    def run(self, host=None, port=None, debug=None, zeroconf=None, **kwargs):
        """Starts the server allowing for runtime parameters. Designed to immitate
        the old Flask app.run style of starting an app

        :param host: Host IP address. Defaults to 0.0.0.0.
        :type host: string
        :param port: Host port. Defaults to 7485.
        :type port: int
        :param debug: Enable server debug mode. Defaults to False.
        :type debug: bool
        :param zeroconf: Enable the zeroconf (mDNS) server. Defaults to True.
        :type zeroconf: bool
        """
        if port is not None:
            self.port = int(port)

        if host is not None:
            self.host = str(host)

        if debug is not None:
            self.debug = debug

        if zeroconf is not None:
            self.zeroconf = zeroconf

        self.start()
