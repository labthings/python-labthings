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

    # Internal methods used by condition variables

    def _acquire_restore(self, count_owner):
        count, owner = count_owner
        self._block.acquire()
        self._count = count
        self._owner = owner

    def _release_save(self):
        count = self._count
        self._count = 0
        owner = self._owner
        self._owner = None
        self._block.release()
        return (count, owner)

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
