from geventwebsocket.handler import WebSocketHandler as _WebSocketHandler

from logging import getLogger, StreamHandler, getLoggerClass, Formatter, DEBUG


def create_logger(name, handlers=None, debug=False):
    if not handlers:
        handlers = ()

    logger = getLogger(name)

    for handler in handlers:
        logger.addHandler(handler)

    return logger


class WebSocketHandler(_WebSocketHandler):
    @property
    def logger(self):
        if not hasattr(self, "_logger"):
            if hasattr(self.server, "log"):
                self._logger = create_logger(__name__, handlers=(self.server.log,))
            else:
                self._logger = create_logger(__name__)

        return self._logger
