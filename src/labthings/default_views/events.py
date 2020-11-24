from ..schema import LogRecordSchema
from ..views import EventView


class LoggingEventView(EventView):
    """List of latest logging events from the session"""

    schema = LogRecordSchema()
