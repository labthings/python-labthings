from gevent.hub import getcurrent
from gevent.lock import RLock as _RLock

from contextlib import contextmanager
import logging

from .exceptions import LockError

sentinel = object()


class RLock(_RLock):
    def locked(self):
        return self._block.locked()


class StrictLock:
    """
    Class that behaves like a Python RLock,
    but with stricter timeout conditions and custom exceptions.

    Args:
        timeout (int): Time in seconds acquisition will wait before raising an exception

    Attributes:
        _lock (:py:class:`threading.RLock`): Parent RLock object
        timeout (int): Time in seconds acquisition will wait before raising an exception
    """

    def __init__(self, timeout=None, name=None):
        self._lock = RLock()
        self.timeout = timeout
        self.name = name

    @contextmanager
    def __call__(self, timeout=sentinel, blocking=True):
        result = self.acquire(timeout=timeout, blocking=blocking)
        yield result
        if result:
            self.release()
        
    def locked(self):
        return self._lock.locked()

    def acquire(self, blocking=True, timeout=sentinel, _strict=True):
        if timeout is sentinel:
            timeout = self.timeout
        result = self._lock.acquire(blocking, timeout=timeout)
        if _strict and not result:
            raise LockError("ACQUIRE_ERROR", self)
        else:
            return result

    def __enter__(self):
        return self.acquire(blocking=True, timeout=self.timeout)

    def __exit__(self, *args):
        self.release()

    def release(self):
        self._lock.release()

    @property
    def _owner(self):
        return self._lock._owner

    @_owner.setter
    def _owner(self, new_owner):
        self._lock._owner = new_owner

    def _is_owned(self):
        return self._lock._is_owned()


class CompositeLock:
    """
    Class that behaves like a :py:class:`labthings.core.lock.StrictLock`,
    but allows multiple locks to be acquired and released.

    Args:
        locks (list): List of parent RLock objects
        timeout (int): Time in seconds acquisition will wait before raising an exception

    Attributes:
        locks (list): List of parent RLock objects
        timeout (int): Time in seconds acquisition will wait before raising an exception
    """

    def __init__(self, locks, timeout=None):
        self.locks = locks
        self.timeout = timeout

    @contextmanager
    def __call__(self, timeout=sentinel, blocking=True):
        result = self.acquire(timeout=timeout, blocking=blocking)
        yield result
        if result:
            self.release()
        
    def acquire(self, blocking=True, timeout=sentinel):
        if timeout is sentinel:
            timeout = self.timeout

        lock_all = all(
            lock.acquire(blocking=blocking, timeout=timeout, _strict=False)
            for lock in self.locks
        )

        if not lock_all:
            self._emergency_release()
            logging.error(f"Unable to acquire {self} within {timeout} seconds")
            raise LockError("ACQUIRE_ERROR", self)

        return True

    def __enter__(self):
        return self.acquire(blocking=True, timeout=self.timeout)

    def __exit__(self, *args):
        return self.release()

    def release(self):
        # If not all child locks are owner by caller
        if not all(owner is getcurrent() for owner in self._owner):
            raise RuntimeError("cannot release un-acquired lock")
        for lock in self.locks:
            if lock.locked():
                lock.release()

    def _emergency_release(self):
        for lock in self.locks:
            if lock.locked() and lock._is_owned():
                lock.release()

    def locked(self):
        return any(lock.locked() for lock in self.locks)

    @property
    def _owner(self):
        return [lock._owner for lock in self.locks]

    @_owner.setter
    def _owner(self, new_owner):
        for lock in self.locks:
            lock._owner = new_owner

    def _is_owned(self):
        return all(lock._is_owned() for lock in self.locks)
