import time
import logging

import threading
from _thread import get_ident


class ClientEvent(object):
    """An event-signaller object with per-client setting and waiting.
    
    A client can be any Greenlet or native Thread. This can be used, for example,
    to signal to clients that new data is available


    """

    def __init__(self):
        self.events = {}
        self._setting_lock = threading.Lock()

    def wait(self, timeout: int = 5):
        """Wait for the next data frame (invoked from each client's thread).

        :param timeout: int:  (Default value = 5)

        """
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]

        return self.events[ident][0].wait(timeout=timeout)

    def set(self, timeout=5):
        """Signal that a new frame is available.

        :param timeout:  (Default value = 5)

        """
        with self._setting_lock:
            now = time.time()
            remove_keys = set()
            for event_key in list(self.events.keys()):
                if not self.events[event_key][0].is_set():
                    # if this client's event is not set, then set it
                    # also update the last set timestamp to now
                    self.events[event_key][0].set()
                    self.events[event_key][1] = now
                else:
                    # if the client's event is already set, it means the client
                    # did not process a previous frame
                    # if the event stays set for more than `timeout` seconds, then
                    # assume the client is gone and remove it
                    if now - self.events[event_key][1] >= timeout:
                        remove_keys.add(event_key)
            if remove_keys:
                for remove_key in remove_keys:
                    del self.events[remove_key]

    def clear(self):
        """Clear frame event, once processed."""
        ident = get_ident()
        if ident not in self.events:
            logging.error(f"Mismatched ident. Current: {ident}, available:")
            logging.error(self.events.keys())
            return False
        self.events[get_ident()][0].clear()
        return True
