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

Two key methods are :meth:`labthings.LabThing.build_property` and :meth:`labthings.LabThing.build_action`. These methods allow the automation creation of Property and Action API views from Python object attributes and methods. By passing schemas to these methods, argument and response marshalling is automatically performed. Offloading actions to background threads is also handled automatically.

.. automethod:: labthings.LabThing.build_property
   :noindex:

.. automethod:: labthings.LabThing.build_action
   :noindex:


Server
------

The integrated server actually handles 3 distinct server functions: WSGI HTTP requests, routing WebSocket requests to the threaded handler, and registering mDNS records for automatic Thing discovery. It is therefore strongly suggested you use the builtin server.

**Important notes:** 

The integrated server will spawn a new native thread *per-connection*. This will only function well in situations where few (<50) simultaneous connections are expected, such as local Web of Things devices. Do not use this server in any public web app where many connections are expected. It is designed exclusively with low-traffic LAN access in mind.

.. autoclass:: labthings.Server
   :members:
   :noindex: