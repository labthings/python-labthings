from labthings.server import wsgi

import logging
import gevent


def test_server_init(thing):
    server = wsgi.Server(thing.app)
    assert server.labthing is thing


def test_server_start(thing):
    server = wsgi.Server(thing.app, host="127.0.0.1", port=5555)

    def start_server():
        server.run()

    gevent.spawn(start_server)
    server.started_event.wait()
    server.stop()


def test_server_run(thing):
    server = wsgi.Server(thing.app)

    def start_server():
        server.run(
            host="127.0.0.1",
            port=5556,
            log=logging.getLogger(),
            debug=False,
            zeroconf=False,
        )

    gevent.spawn(start_server)
    server.started_event.wait()
    server.stop()


def test_server_start_no_labthing(app):
    server = wsgi.Server(app, host="127.0.0.1", port=5557)

    def start_server():
        server.run()

    gevent.spawn(start_server)
    server.started_event.wait()
    server.stop()


def test_server_stop_before_run(thing):
    server = wsgi.Server(thing.app, host="127.0.0.1", port=5558,)
    server.stop()
