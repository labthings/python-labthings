"""A super simple EventEmitter implementation.

   Modified slightly from: https://github.com/axetroy/pyee
"""


class EventEmitter:
    def __init__(self):
        self._events = {}

    def on(self, event, handler):
        events = self._events
        if event not in events:
            events[event] = []
        events[event].append(handler)

    def emit(self, event, *data):
        events = self._events
        if event not in events:
            return
        handlers = events[event]
        for handler in handlers:
            handler(data)


class Value(EventEmitter):
    """
    A property value.

    This is used for communicating between the Thing representation and the
    actual physical thing implementation.

    Notifies all observers when the underlying value changes through an
    external update (command to turn the light off) or if the underlying sensor
    reports a new value.
    """

    def __init__(self, initial_value=None, read_forwarder=None, write_forwarder=None):
        """
        Initialize the object.

        initial_value -- the initial value
        value_forwarder -- the method that updates the actual value on the
                           thing
        """
        EventEmitter.__init__(self)
        self._value = initial_value
        self.read_forwarder = read_forwarder
        self.write_forwarder = write_forwarder

    @property
    def readonly(self):
        return self.read_forwarder and not self.write_forwarder

    @property
    def writeonly(self):
        return self.write_forwarder and not self.read_forwarder

    def set(self, value):
        """
        Set a new value for this thing.

        value -- value to set
        """
        if self.write_forwarder is not None:
            self.write_forwarder(value)

        self.notify_of_external_update(value)
        return value

    def get(self):
        """Return the last known value from the underlying thing."""
        if self.read_forwarder:
            self._value = self.read_forwarder()
        return self._value

    def notify_of_external_update(self, value):
        """
        Notify observers of a new value.

        value -- new value
        """
        if value is not None and value != self._value:
            self._value = value
            self.emit("update", value)
