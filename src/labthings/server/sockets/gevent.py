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

from flask.helpers import _endpoint_from_view_func
from werkzeug.routing import Map, Rule, BuildError

from ..representations import encode_json


class SocketSubscriber:
    def __init__(self, ws):
        self.ws = ws

    def emit(self, event: dict):
        response = encode_json(event)
        # TODO: Logic surrounding if this subscriber is subscribed to the requested event type
        self.ws.send(response)


class WsUrlAdapterWrapper(object):
    def __init__(self, app_adapter, sockets_adapter):
        self.__app_adapter = app_adapter
        self.__sockets_adapter = sockets_adapter

    def build(
        self,
        endpoint,
        values=None,
        method=None,
        force_external=False,
        append_unknown=True,
    ):
        try:
            return (
                "ws"
                + self.__sockets_adapter.build(
                    endpoint=endpoint,
                    values=values,
                    method=None,
                    force_external=True,
                    append_unknown=append_unknown,
                )[4:]
            )
        except BuildError:
            return self.__app_adapter.build(
                endpoint=endpoint,
                values=values,
                method=method,
                force_external=force_external,
                append_unknown=append_unknown,
            )

    def __getattr__(self, attr):
        fun = getattr(self.__app_adapter, attr)
        setattr(self, attr, fun)
        return fun


class Sockets:
    def __init__(self, app=None):
        #: Compatibility with 'Flask' application.
        #: The :class:`~werkzeug.routing.Map` for this instance. You can use
        #: this to change the routing converters after the class was created
        #: but before any routes are connected.
        self.url_map = Map()

        #: Compatibility with 'Flask' application.
        #: All the attached blueprints in a dictionary by name. Blueprints
        #: can be attached multiple times so this dictionary does not tell
        #: you how often they got attached.
        self.blueprints = {}
        self._blueprint_order = []

        self.view_functions = {}

        if app:
            self.init_app(app)

    def __create_url_adapter(self, url_map, request):
        if request is not None:
            return url_map.bind_to_environ(
                request.environ, server_name=self.app.config["SERVER_NAME"]
            )
        elif self.app.config["SERVER_NAME"] is not None:
            return url_map.bind(
                self.app.config["SERVER_NAME"],
                script_name=self.app.config["APPLICATION_ROOT"] or "/",
                url_scheme=self.app.config["PREFERRED_URL_SCHEME"],
            )

    def create_url_adapter(self, request):
        adapter_for_app = self.__create_url_adapter(self.app.url_map, request)
        adapter_for_sockets = self.__create_url_adapter(self.url_map, request)
        return WsUrlAdapterWrapper(adapter_for_app, adapter_for_sockets)

    def init_app(self, app):
        self.app = app
        self.app_wsgi_app = app.wsgi_app

        app.wsgi_app = self.wsgi_app
        app.create_url_adapter = self.create_url_adapter

    def route(self, rule, **options):
        def decorator(f):
            endpoint = options.pop("endpoint", None)
            self.add_url_rule(rule, endpoint, f, **options)
            return f

        return decorator

    def add_url_rule(self, rule, endpoint, f, **options):
        if endpoint is None:
            endpoint = _endpoint_from_view_func(f)

        methods = options.pop("methods", None)

        setattr(f, "endpoint", endpoint)

        self.url_map.add(Rule(rule, endpoint=endpoint, **options))
        self.view_functions[endpoint] = f

        if methods is None:
            methods = []
        self.app.add_url_rule(rule, endpoint, f, methods=methods, **options)

    def add_view(self, url, f, endpoint=None, **options):
        return self.add_url_rule(url, endpoint, f, **options)

    def register_blueprint(self, blueprint, **options):
        """
        Registers a blueprint for web sockets like for 'Flask' application.
        Decorator :meth:`~flask.app.setupmethod` is not applied, because it
        requires ``debug`` and ``_got_first_request`` attributes to be defined.
        """
        first_registration = False

        if blueprint.name in self.blueprints:
            assert self.blueprints[blueprint.name] is blueprint, (
                "A blueprint's name collision occurred between %r and "
                '%r.  Both share the same name "%s".  Blueprints that '
                "are created on the fly need unique names."
                % (blueprint, self.blueprints[blueprint.name], blueprint.name)
            )
        else:
            self.blueprints[blueprint.name] = blueprint
            self._blueprint_order.append(blueprint)
            first_registration = True

        blueprint.register(self, options, first_registration)

    def wsgi_app(self, environ, start_response):
        adapter = self.url_map.bind_to_environ(environ)
        try:
            # Find handler view function
            endpoint, values = adapter.match()
            handler = self.view_functions[endpoint]

            # Handle environment
            environment = environ["wsgi.websocket"]
            cookie = None
            if "HTTP_COOKIE" in environ:
                cookie = parse_cookie(environ["HTTP_COOKIE"])

            with self.app.app_context():
                with self.app.request_context(environ):
                    # add cookie to the request to have correct session handling
                    request.cookie = cookie
                    # Run WebSocket handler
                    handler(environment, **values)
                    return []
        except (NotFound, KeyError):
            return self.app_wsgi_app(environ, start_response)
