import gevent
import socket
import signal
import logging
from werkzeug.debug import DebuggedApplication

from zeroconf import IPVersion, ServiceInfo, Zeroconf, get_all_addresses

from .handler import WebSocketHandler
from ..find import current_labthing

sentinel = object()


class Server:
    def __init__(
        self,
        app,
        host="0.0.0.0",
        port=7485,
        log=sentinel,
        error_log=sentinel,
        debug=False,
        zeroconf=True,
    ):
        self.app = app
        # Find LabThing attached to app
        self.labthing = current_labthing(app)

        # Server properties
        self.host = host
        self.port = port
        self.log = log
        self.error_log = error_log
        self.debug = debug
        self.zeroconf = zeroconf

        # Servers
        self.wsgi_server = None
        self.zeroconf_server = None
        self.service_info = None
        self.service_infos = []

        # Events
        self.started_event = gevent.event.Event()

    def register_zeroconf(self):
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
        if self.started_event.is_set():
            self.started_event.clear()
        logging.info("Done")

    def start(self):
        # Unmodified version of app
        app_to_run = self.app

        # Handle zeroconf
        if self.zeroconf:
            self.register_zeroconf()

        # Handle logging
        if self.log is sentinel:
            print("No access log specified. Using root.")
            self.log = logging.getLogger()
        if not self.log:
            self.log = logging.NullHandler()
        if self.error_log is sentinel:
            print("No error og specified. Using root.")
            self.error_log = logging.getLogger()
        if not self.error_log:
            self.error_log = logging.NullHandler()

        # Handle debug mode
        if self.debug:
            self.log.setLevel(logging.DEBUG)
            app_to_run = DebuggedApplication(self.app)
            logging.getLogger("zeroconf").setLevel(logging.DEBUG)

        # Slightly more useful logger output
        friendlyhost = "localhost" if self.host == "0.0.0.0" else self.host
        print("Starting LabThings WSGI Server")
        print(f"Debug mode: {self.debug}")
        print(f"Access log: {self.log}")
        print(f"Error log: {self.error_log}")
        print(f"Running on http://{friendlyhost}:{self.port} (Press CTRL+C to quit)")

        # Create WSGIServer
        self.wsgi_server = gevent.pywsgi.WSGIServer(
            (self.host, self.port),
            app_to_run,
            handler_class=WebSocketHandler,
            log=self.log,
            error_log=self.error_log,
        )

        # Serve
        gevent.signal_handler(signal.SIGTERM, self.stop)

        # Set started event
        self.started_event.set()
        try:
            self.wsgi_server.serve_forever()
        except (KeyboardInterrupt, SystemExit):  # pragma: no cover
            logging.warning(
                "Terminating by KeyboardInterrupt or SystemExit"
            )  # pragma: no cover
            self.stop()  # pragma: no cover

    def run(
        self,
        host=None,
        port=None,
        log=sentinel,
        error_log=sentinel,
        debug=None,
        zeroconf=None,
    ):
        """Starts the server allowing for runtime parameters. Designed to immitate
        the old Flask app.run style of starting an app

        Args:
            host (string, optional): Host IP address. Defaults to None.
            port (int, optional): Host port. Defaults to None.
            log (optional): Logger to log to. Defaults to None.
            debug (bool, optional): Enable server debug mode. Defaults to None.
            zeroconf (bool, optional): Enable the zeroconf server. Defaults to None.
        """
        if port is not None:
            self.port = int(port)

        if host is not None:
            self.host = str(host)

        if log is not sentinel:
            self.log = log

        if error_log is not sentinel:
            self.error_log = error_log

        if debug is not None:
            self.debug = debug

        if zeroconf is not None:
            self.zeroconf = zeroconf

        self.start()
