from gevent.hub import getcurrent
from gevent.lock import RLock as _RLock

from .exceptions import LockError


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

    def __init__(self, timeout=1, name=None):
        self._lock = RLock()
        self.timeout = timeout
        self.name = name

    def locked(self):
        return self._lock.locked()

    def acquire(self, blocking=True, timeout=None, _strict=True):
        if not timeout:
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

    def __init__(self, locks, timeout=1):
        self.locks = locks
        self.timeout = timeout

    def acquire(self, blocking=True, timeout=None):
        if not timeout:
            timeout = self.timeout

        lock_all = all(
            lock.acquire(blocking=blocking, timeout=timeout, _strict=False)
            for lock in self.locks
        )

        if not lock_all:
            self._emergency_release()
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
