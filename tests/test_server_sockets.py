from labthings.server.sockets import base, gevent as gsocket

import json
from flask import Blueprint
from werkzeug.routing import Map


def test_socket_subscriber_property_notify(view_cls, fake_websocket):
    setattr(view_cls, "endpoint", "index")
    ws = fake_websocket("", recieve_once=True)
    sub = base.SocketSubscriber(ws)

    sub.property_notify(view_cls)
    assert json.loads(ws.response) == {
        "messageType": "propertyStatus",
        "data": {"index": "GET"},
    }


def test_socket_subscriber_property_notify_empty_view(flask_view_cls, fake_websocket):
    ws = fake_websocket("", recieve_once=True)
    sub = base.SocketSubscriber(ws)

    sub.property_notify(flask_view_cls)
    assert json.loads(ws.response) == {
        "messageType": "propertyStatus",
        "data": {flask_view_cls.__name__: None},
    }


def test_socket_subscriber_event_notify(fake_websocket):
    ws = fake_websocket("", recieve_once=True)
    sub = base.SocketSubscriber(ws)

    data = {"key": "value"}

    sub.event_notify(data)
    assert json.loads(ws.response) == {"messageType": "event", "data": data}


def test_sockets_flask_init(app):
    original_wsgi_app = app.wsgi_app
    socket = gsocket.Sockets(app)
    assert socket
    # Check new wsgi_app
    assert isinstance(app.wsgi_app, gsocket.SocketMiddleware)
    # Check "fallback" wsgi_app. This should be the original app.wsgi_app
    assert app.wsgi_app.wsgi_app == original_wsgi_app


def test_sockets_flask_delayed_init(app):
    original_wsgi_app = app.wsgi_app
    socket = gsocket.Sockets()
    socket.init_app(app)
    assert socket
    # Check new wsgi_app
    assert isinstance(app.wsgi_app, gsocket.SocketMiddleware)
    # Check "fallback" wsgi_app. This should be the original app.wsgi_app
    assert app.wsgi_app.wsgi_app == original_wsgi_app


def test_sockets_flask_route(app):
    socket = gsocket.Sockets(app)

    @socket.route("/ws")
    def ws_view_func(ws):
        pass

    # Assert ws_view_func was added to the Sockets URL map
    passed = False
    for rule in socket.url_map.iter_rules():
        if rule.endpoint == ws_view_func:
            passed = True
    assert passed


def test_sockets_flask_blueprint(app):
    socket = gsocket.Sockets(app)

    bp = Blueprint("blueprint", __name__)

    @bp.route("/ws")
    def ws_view_func(ws):
        pass

    socket.register_blueprint(bp, url_prefix="/")

    # Assert ws_view_func was added to the Sockets URL map
    passed = False
    for rule in socket.url_map.iter_rules():
        if rule.endpoint == ws_view_func:
            passed = True
    assert passed

    # Test re-register same blueprint (should pass)
    socket.register_blueprint(bp, url_prefix="/")


### Will need regular updating as new message handlers are added
def test_process_socket_message():
    assert base.process_socket_message("message") is None
    assert base.process_socket_message(None) is None
