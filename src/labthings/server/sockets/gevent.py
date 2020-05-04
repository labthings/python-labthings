"""
Once upon a time, based on flask-websocket; Copyright (C) 2013 Kenneth Reitz
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# -*- coding: utf-8 -*-

from werkzeug.exceptions import NotFound
from werkzeug.http import parse_cookie
from flask import request
import gevent

from .base import BaseSockets, process_socket_message


class SocketMiddleware(object):
    def __init__(self, wsgi_app, app, socket):
        self.ws = socket
        self.app = app
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        adapter = self.ws.url_map.bind_to_environ(environ)

        if environ.get("HTTP_UPGRADE") == "websocket":
            try:  # Try matching to a Sockets route
                handler, values = adapter.match()
                environment = environ["wsgi.websocket"]
                cookie = None
                if "HTTP_COOKIE" in environ:
                    cookie = parse_cookie(environ["HTTP_COOKIE"])

                with self.app.app_context():
                    with self.app.request_context(environ):
                        # add cookie to the request to have correct session handling
                        request.cookie = cookie

                        handler(environment, **values)
                        return []
            except (NotFound, KeyError):
                return self.wsgi_app(environ, start_response)
        else:  # If not upgrading to a websocket
            return self.wsgi_app(environ, start_response)


class Sockets(BaseSockets):
    def init_app(self, app):
        app.wsgi_app = SocketMiddleware(app.wsgi_app, app, self)


def socket_handler_loop(ws):
    while not ws.closed:
        message = ws.receive()
        if message is None:
            break
        response = process_socket_message(message)
        if response:
            ws.send(response)
        gevent.sleep(0.1)
