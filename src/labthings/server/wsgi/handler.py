from geventwebsocket.handler import WebSocketHandler as _WebSocketHandler

from logging import getLogger, StreamHandler, getLoggerClass, Formatter, DEBUG


def create_logger(name, handlers=None):
    """Created a logger object from a list of log handlers

    Args:
        name (str): Name for the logger
        handlers ([logging.Handler], optional): [List of log handlers]. Defaults to None.

    Returns:
        [logging.Logger]: Logger object containing the passed handlers
    """
    if not handlers:
        handlers = ()

    logger = getLogger(name)

    for handler in handlers:
        logger.addHandler(handler)

    return logger


class WebSocketHandler(_WebSocketHandler):
    """
    Override geventwebsocket.handler.WebSocketHandler logger behaviour.
    This allows geventwebsocket to properly interact with the 
    gevent.pywsgi.WSGIServer logger.
    """

    @property
    def logger(self):
        if not hasattr(self, "_logger"):
            if hasattr(self.server, "log"):
                self._logger = create_logger(__name__, handlers=(self.server.log,))
            else:
                self._logger = create_logger(__name__)

        return self._logger
