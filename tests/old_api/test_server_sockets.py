from labthings import sockets
from flask import Blueprint


def test_sockets_flask_init(app):
    original_wsgi_app = app.wsgi_app
    socket = sockets.Sockets(app)
    assert socket
    # Check "fallback" wsgi_app. This should be the original app.wsgi_app
    assert socket.app_wsgi_app == original_wsgi_app


def test_sockets_flask_delayed_init(app):
    original_wsgi_app = app.wsgi_app
    socket = sockets.Sockets()
    socket.init_app(app)
    assert socket
    # Check "fallback" wsgi_app. This should be the original app.wsgi_app
    assert socket.app_wsgi_app == original_wsgi_app


def test_sockets_flask_route(app):
    socket = sockets.Sockets(app)

    @socket.route("/ws", endpoint="ws")
    def ws_view_func(ws):
        pass

    # Assert ws_view_func was added to the Sockets URL map
    passed = False
    for rule in socket.url_map.iter_rules():
        if rule.endpoint == "ws":
            passed = True
    assert passed


def test_sockets_flask_blueprint(app):
    socket = sockets.Sockets(app)

    bp = Blueprint("blueprint", __name__)

    @bp.route("/ws", endpoint="ws")
    def ws_view_func(ws):
        pass

    socket.register_blueprint(bp, url_prefix="/")

    # Assert ws_view_func was added to the Sockets URL map
    passed = False
    for rule in socket.url_map.iter_rules():
        print(rule.endpoint)
        if rule.endpoint == "blueprint.ws":
            passed = True
    assert passed

    # Test re-register same blueprint (should pass)
    socket.register_blueprint(bp, url_prefix="/")


def test_socket_middleware_http(app, client):
    socket = sockets.Sockets(app)

    @socket.route("/")
    def ws_view_func(ws):
        ws.send("WS")

    @app.route("/")
    def http_view_func():
        return "GET"

    # Assert ws_view_func was added to the Sockets URL map
    with client as c:
        assert c.get("/").data == b"GET"


def test_socket_middleware_ws(app, ws_client):
    socket = sockets.Sockets(app)

    @socket.route("/<param>")
    def ws_view_func(ws, param):
        msg = ws.recieve()
        ws.send(msg)

    # Assert ws_view_func was added to the Sockets URL map
    with ws_client as c:
        assert c.connect("/test", message="hello") == ["hello"]


def test_socket_middleware_add_view(app, ws_client):
    socket = sockets.Sockets(app)

    def ws_view_func(ws):
        msg = ws.recieve()
        ws.send(msg)

    socket.add_view("/", ws_view_func)

    # Assert ws_view_func was added to the Sockets URL map
    with ws_client as c:
        assert c.connect("/", message="hello") == ["hello"]


def test_socket_middleware_http_fallback(app, ws_client):
    sockets.Sockets(app)

    @app.route("/")
    def http_view_func():
        return "GET"

    # Assert ws_view_func was added to the Sockets URL map
    with ws_client as c:
        assert c.get("/").data == b"GET"


def test_socket_middleware_ws_http_cookie(app, ws_client):
    socket = sockets.Sockets(app)

    @socket.route("/")
    def ws_view_func(ws):
        msg = ws.recieve()
        ws.send(msg)

    # Assert ws_view_func was added to the Sockets URL map
    with ws_client as c:
        c.environ_base["HTTP_COOKIE"] = {"key": "value"}
        assert c.connect("/", message="hello") == ["hello"]