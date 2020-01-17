from threading import RLock

from .exceptions import LockError


class StrictLock(object):
    """
    Class that behaves like a Python RLock, but with stricter timeout conditions and custom exceptions.

    Args:
        timeout (int): Time, in seconds, lock acquisition will wait before raising an exception

    Attributes:
        _lock (:py:class:`threading.RLock`): Parent RLock object
        timeout (int): Time, in seconds, lock acquisition will wait before raising an exception
    """

    def __init__(self, timeout=1):
        self._lock = RLock()
        self.timeout = timeout

    def locked(self):
        return self._lock.locked()

    def acquire(self, blocking=True):
        return self._lock.acquire(blocking, timeout=self.timeout)

    def __enter__(self):
        result = self._lock.acquire(blocking=True, timeout=self.timeout)
        if result:
            return result
        else:
            raise LockError("ACQUIRE_ERROR", self)

    def __exit__(self, *args):
        self._lock.release()

    def release(self):
        self._lock.release()


class CompositeLock(object):
    """
    Class that behaves like a :py:class:`labthings.core.lock.StrictLock`,
    but allows multiple locks to be acquired and released.

    Args:
        locks (list): List of parent RLock objects
        timeout (int): Time, in seconds, lock acquisition will wait before raising an exception

    Attributes:
        locks (list): List of parent RLock objects
        timeout (int): Time, in seconds, lock acquisition will wait before raising an exception
    """

    def __init__(self, locks, timeout=1):
        self.locks = locks
        self.timeout = timeout

    def acquire(self, blocking=True):
        return (lock.acquire(blocking=blocking) for lock in self.locks)

    def __enter__(self):
        result = (lock.acquire(blocking=True) for lock in self.locks)
        if all(result):
            return result
        else:
            raise LockError("ACQUIRE_ERROR", self)

    def __exit__(self, *args):
        for lock in self.locks:
            lock.release()

    def release(self):
        for lock in self.locks:
            lock.release()
