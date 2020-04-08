from gevent.hub import getcurrent
from gevent._semaphore import Semaphore

from .exceptions import LockError


class RLock(object):
    """
    A mutex that can be acquired more than once by the same greenlet.
    A mutex can only be locked by one greenlet at a time. A single greenlet
    can `acquire` the mutex as many times as desired, though. Each call to
    `acquire` must be paired with a matching call to `release`.
    It is an error for a greenlet that has not acquired the mutex
    to release it.
    Instances are context managers.
    """

    __slots__ = ("_block", "_owner", "_count", "__weakref__")

    def __init__(self):
        self._block = Semaphore(1)
        self._owner = None
        self._count = 0

    def __repr__(self):
        return "<%s at 0x%x _block=%s _count=%r _owner=%r)>" % (
            self.__class__.__name__,
            id(self),
            self._block,
            self._count,
            self._owner,
        )

    def locked(self):
        return self._block.locked()

    def acquire(self, blocking=True, timeout=None):
        """
        Acquire the mutex, blocking if *blocking* is true, for up to
        *timeout* seconds.
        .. versionchanged:: 1.5a4
           Added the *timeout* parameter.
        :return: A boolean indicating whether the mutex was acquired.
        """
        me = getcurrent()
        if self._owner is me:
            self._count = self._count + 1
            return 1
        rc = self._block.acquire(blocking, timeout)
        if rc:
            self._owner = me
            self._count = 1
        return rc

    def __enter__(self):
        return self.acquire()

    def release(self):
        """
        Release the mutex.
        Only the greenlet that originally acquired the mutex can
        release it.
        """
        if self._owner is not getcurrent():
            raise RuntimeError("cannot release un-acquired lock")
        self._count = count = self._count - 1
        if not count:
            self._owner = None
            self._block.release()

    def __exit__(self, typ, value, tb):
        self.release()

    def _is_owned(self):
        return self._owner is getcurrent()


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
            [
                lock.acquire(blocking=blocking, timeout=timeout, _strict=False)
                for lock in self.locks
            ]
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
        if not all([owner is getcurrent() for owner in self._owner]):
            raise RuntimeError("cannot release un-acquired lock")
        for lock in self.locks:
            if lock.locked():
                lock.release()

    def _emergency_release(self):
        for lock in self.locks:
            if lock.locked() and lock._is_owned():
                lock.release()

    def locked(self):
        return any([lock.locked() for lock in self.locks])

    @property
    def _owner(self):
        return [lock._owner for lock in self.locks]

    @_owner.setter
    def _owner(self, new_owner):
        for lock in self.locks:
            lock._owner = new_owner

    def _is_owned(self):
        return all([lock._is_owned() for lock in self.locks])
