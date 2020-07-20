from collections import deque as _deque


class Deque(_deque):
    """ """
    def __init__(self, iterable=None, maxlen=100):
        _deque.__init__(self, iterable or [], maxlen)


def resize_deque(iterable: _deque, newsize: int):
    """

    :param iterable: _deque: 
    :param newsize: int: 

    """
    return deque(iterable, newsize)
