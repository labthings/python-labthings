# -*- coding: utf-8 -*-

from werkzeug.routing import Map, Rule
from werkzeug.exceptions import NotFound
from werkzeug.http import parse_cookie
from flask import request, current_app
import logging
from abc import ABC, abstractmethod

from ..representations import encode_json


class SocketSubscriber:
    def __init__(self, ws):
        self.ws = ws

    def property_notify(self, viewcls):
        if hasattr(viewcls, "get_value") and callable(viewcls.get_value):
            property_value = viewcls().get_value()
        else:
            property_value = None

        property_name = getattr(viewcls, "endpoint", None) or getattr(
            viewcls, "__name__", "unknown"
        )

        response = encode_json(
            {"messageType": "propertyStatus", "data": {property_name: property_value}}
        )

        self.ws.send(response)

    def event_notify(self, event_dict: dict):
        response = encode_json({"messageType": "event", "data": event_dict})

        self.ws.send(response)


class BaseSockets(ABC):
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

        if app:
            self.init_app(app)

    @abstractmethod
    def init_app(self, app):
        "Registers Flask middleware"

    def route(self, rule, **options):
        def decorator(f):
            endpoint = options.pop("endpoint", None)
            self.add_url_rule(rule, endpoint, f, **options)
            return f

        return decorator

    def add_url_rule(self, rule, _, f, **options):
        self.url_map.add(Rule(rule, endpoint=f))

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


def process_socket_message(message: str):
    if message:
        return None
    else:
        return None
