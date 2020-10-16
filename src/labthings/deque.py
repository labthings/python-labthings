from collections import deque as _deque
from threading import Lock


class Deque(_deque):
    """ """

    def __init__(self, iterable=None, maxlen=100):
        _deque.__init__(self, iterable or [], maxlen)


class LockableDeque(Deque):
    def __init__(self, iterable=None, maxlen=100, timeout=-1):
        Deque.__init__(self, iterable, maxlen)
        self.lock = Lock()
        self.timeout = timeout

    def __enter__(self):
        self.lock.acquire(blocking=True, timeout=self.timeout)
        return self

    def __exit__(self, *args):
        self.lock.release()


def resize_deque(iterable: _deque, newsize: int):
    """

    :param iterable: _deque:
    :param newsize: int:

    """
    return Deque(iterable, newsize)
