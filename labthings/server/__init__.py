import logging

EXTENSION_NAME = "flask-labthings"

# Monkey patching is bad and should never be done
# import eventlet
# eventlet.monkey_patch()

from gevent import monkey

monkey.patch_all()
