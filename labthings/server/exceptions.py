from flask import jsonify, escape
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException


class JSONExceptionHandler:

    """
    A class to be registered as a Flask error handler,
    converts error codes into a JSON response
    """

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def std_handler(self, error):
        if isinstance(error, HTTPException):
            message = error.description
        elif hasattr(error, "message"):
            message = error.message
        else:
            message = str(error)

        status_code = error.code if isinstance(error, HTTPException) else 500

        response = {"code": status_code, "message": escape(message)}
        return jsonify(response), status_code

    def init_app(self, app):
        self.app = app
        self.register(HTTPException)
        for code, v in default_exceptions.items():
            self.register(code)

    def register(self, exception_or_code, handler=None):
        self.app.errorhandler(exception_or_code)(handler or self.std_handler)
