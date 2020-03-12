# -*- coding: utf-8 -*-

from werkzeug.exceptions import NotFound
from werkzeug.http import parse_cookie
from werkzeug.wrappers import Request
from flask import request
from pprint import pformat
import logging

from .base import BaseSockets, process_socket_message
from eventlet import websocket
import eventlet


class SocketMiddleware(object):
    def __init__(self, wsgi_app, app, socket):
        self.ws = socket
        self.app = app
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        request = Request(environ)
        adapter = self.ws.url_map.bind_to_environ(environ)

        logging.debug(pformat(environ))

        if environ.get("HTTP_UPGRADE") == "websocket":
            try:  # Try matching to a Sockets route
                handler, values = adapter.match()
                cookie = None
                if "HTTP_COOKIE" in environ:
                    cookie = parse_cookie(environ["HTTP_COOKIE"])

                with self.app.app_context():
                    with self.app.request_context(environ):
                        # add cookie to the request to have correct session handling
                        request.cookie = cookie

                        websocket.WebSocketWSGI(handler)(
                            environ, start_response, **values
                        )
                        return []
            except (NotFound, KeyError):  # If no socket route found, fall back to WSGI
                return self.wsgi_app(environ, start_response)
        else:  # If not upgrading to a websocket
            return self.wsgi_app(environ, start_response)


class Sockets(BaseSockets):
    def init_app(self, app):
        app.wsgi_app = SocketMiddleware(app.wsgi_app, app, self)


def socket_handler_loop(ws):
    while True:
        message = ws.wait()
        if message is None:
            break
        response = process_socket_message(message)
        if response:
            ws.send(response)
