from gevent.hub import getcurrent
import gevent
import time
import logging

from gevent.monkey import get_original
from gevent.lock import BoundedSemaphore

# Guarantee that Task threads will always be proper system threads, regardless of Gevent patches
Event = get_original("threading", "Event")


class ClientEvent(object):
    """
    An event-signaller object with per-client setting and waiting.

    A client can be any Greenlet or native Thread. This can be used, for example,
    to signal to clients that new data is available
    """

    def __init__(self):
        self.events = {}
        self._setting_lock = BoundedSemaphore()

    def wait(self, timeout: int = 5):
        """Wait for the next data frame (invoked from each client's thread)."""
        ident = id(getcurrent())
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [Event(), time.time()]

        # We have to reimplement event waiting here as we need native thread events to allow gevent context switching
        wait_start = time.time()
        while not self.events[ident][0].is_set():
            now = time.time()
            if now - wait_start > timeout:
                return False
            gevent.sleep(0)
        return True

    def set(self, timeout=5):
        """Signal that a new frame is available."""
        with self._setting_lock:
            now = time.time()
            remove_keys = set()
            for ident, event in self.events.items():
                if not event[0].is_set():
                    # if this client's event is not set, then set it
                    # also update the last set timestamp to now
                    event[0].set()
                    event[1] = now
                else:
                    # if the client's event is already set, it means the client
                    # did not process a previous frame
                    # if the event stays set for more than `timeout` seconds, then
                    # assume the client is gone and remove it
                    if now - event[1] >= timeout:
                        remove_keys.add(ident)
            if remove_keys:
                for ident in remove_keys:
                    del self.events[ident]

    def clear(self):
        """Clear frame event, once processed."""
        ident = id(getcurrent())
        if ident not in self.events:
            logging.error(f"Mismatched ident. Current: {ident}, available:")
            logging.error(self.events.keys())
            return False
        self.events[id(getcurrent())][0].clear()
        return True
