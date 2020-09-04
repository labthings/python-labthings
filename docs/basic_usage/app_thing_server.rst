App, LabThing, and Server
=========================

Python LabThings works as a Flask extension, and so we introduce two key objects: the :class:`flask.Flask` app, and the :class:`labthings.LabThing` object. The :class:`labthings.LabThing` object is our main entrypoint for the Flask application, and all LabThings functionality is added via this object.

In order to enable threaded actions, and concurrent WebSocket connections, the app should be served using the :class:`labthings.Server` class. Other production servers such as Gevent can be used, however this will require monkey-patching and has not been comprehensively tested.


Create app
----------

The :meth:`labthings.create_app` function automatically creates a Flask app object, enables up cross-origin resource sharing, and initialises a :class:`labthings.LabThing` instance on the app. The function returns both in a tuple.

.. autofunction:: labthings.create_app
   :noindex:

ALternatively, the app and :class:`labthings.LabThing` objects can be initialised and attached separately, for example:

.. code-block:: python

   from flask import Flask
   from labthings import LabThing

   app = Flask(__name__)
   labthing = LabThing(app)


LabThing
--------

The LabThing object is our main entrypoint, and handles creating API views, managing background actions, tracking logs, and generating API documentation.

.. autoclass:: labthings.LabThing
   :noindex:


Views
-----

Thing interaction affordances are created using Views. Two main View types correspond to properties and actions.

.. autoclass:: labthings.PropertyView
   :noindex:

.. autoclass:: labthings.ActionView
   :noindex:


Server
------

The integrated server actually handles 3 distinct server functions: WSGI HTTP requests, routing WebSocket requests to the threaded handler, and registering mDNS records for automatic Thing discovery. It is therefore strongly suggested you use the builtin server.

**Important notes:** 

The integrated server will spawn a new native thread *per-connection*. This will only function well in situations where few (<50) simultaneous connections are expected, such as local Web of Things devices. Do not use this server in any public web app where many connections are expected. It is designed exclusively with low-traffic LAN access in mind.

.. autoclass:: labthings.Server
   :members:
   :noindex: