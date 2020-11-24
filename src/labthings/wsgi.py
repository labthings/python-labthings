import hashlib
import socket

from werkzeug.serving import run_simple
from zeroconf import IPVersion, ServiceInfo, Zeroconf, get_all_addresses

from .find import current_labthing

sentinel = object()


class Server:
    """Combined WSGI+mDNS server.

    :param host: Host IP address. Defaults to 0.0.0.0.
    :type host: string
    :param port: Host port. Defaults to 7485.
    :type port: int
    :param debug: Enable server debug mode. Defaults to False.
    :type debug: bool
    :param zeroconf: Enable the zeroconf (mDNS) server. Defaults to True.
    :type zeroconf: bool
    """

    def __init__(self, app, host="0.0.0.0", port=7485, debug=False, zeroconf=True):
        self.app = app
        # Find LabThing attached to app
        with app.app_context():
            self.labthing = current_labthing(app)

        # Server properties
        self.host = host
        self.port = port
        self.debug = debug
        self.zeroconf = zeroconf

        # Servers
        self.zeroconf_server = None
        self.service_info = None
        self.service_infos = []

    def _register_zeroconf(self):
        if self.labthing:
            host = f"{self.labthing.safe_title}._labthing._tcp.local."
            if len(host) > 63:
                host = (
                    f"{hashlib.sha1(host.encode()).hexdigest()}._labthing._tcp.local."
                )
            print(f"Registering zeroconf {host}")
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
                    host,
                    port=self.port,
                    properties={
                        "path": self.labthing.url_prefix,
                        "id": self.labthing.id,
                    },
                    addresses=mdns_addresses,
                )
            )
            self.zeroconf_server = Zeroconf(ip_version=IPVersion.V4Only)
            for service in self.service_infos:
                self.zeroconf_server.register_service(service)

    def start(self):
        """Start the server and register mDNS records"""
        # Handle zeroconf
        if self.zeroconf:
            self._register_zeroconf()

        # Slightly more useful logger output
        friendlyhost = "localhost" if self.host == "0.0.0.0" else self.host
        print("Starting LabThings WSGI Server")
        print(f"Debug mode: {self.debug}")
        print(f"Running on http://{friendlyhost}:{self.port} (Press CTRL+C to quit)")

        # Create WSGIServer
        try:
            run_simple(
                self.host,
                self.port,
                self.app,
                use_debugger=self.debug,
                threaded=True,
                processes=1,
            )
        finally:
            # When server stops
            if self.zeroconf_server:
                print("Unregistering zeroconf services...")
                for service in self.service_infos:
                    self.zeroconf_server.unregister_service(service)
                self.zeroconf_server.close()
            print("Server stopped")

    def run(self, host=None, port=None, debug=None, zeroconf=None):
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
