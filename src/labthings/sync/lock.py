from threading import _RLock, current_thread

from contextlib import contextmanager
import logging

sentinel = object()


class LockError(RuntimeError):
    """ """
    ERROR_CODES = {
        "ACQUIRE_ERROR": "Unable to acquire. Lock in use by another thread.",
        "IN_USE_ERROR": "Lock in use by another thread.",
    }

    def __init__(self, code, lock):
        self.code = code
        if code in LockError.ERROR_CODES:
            self.message = LockError.ERROR_CODES[code]
        else:
            self.message = "Unknown error."

        self.string = f"{self.code}: LOCK {lock}: {self.message}"
        print(self.string)

        RuntimeError.__init__(self)

    def __str__(self):
        return self.string


class StrictLock:
    """Class that behaves like a Python RLock,
    but with stricter timeout conditions and custom exceptions.

    :param timeout: Time in seconds acquisition will wait before raising an exception
    :type timeout: int

    """

    def __init__(self, timeout=-1, name=None):
        self._lock = _RLock()
        self.timeout = timeout
        self.name = name

    @property
    def _owner(self):
        """ """
        return self._lock._owner

    @contextmanager
    def __call__(self, timeout=sentinel, blocking=True):
        result = self.acquire(timeout=timeout, blocking=blocking)
        yield result
        if result:
            self.release()

    def locked(self):
        """ """
        return bool(self._lock._count)

    def acquire(self, blocking=True, timeout=sentinel, _strict=True):
        """

        :param blocking:  (Default value = True)
        :param timeout:  (Default value = sentinel)
        :param _strict:  (Default value = True)

        """
        # If no timeout is given, use object level timeout
        if timeout is sentinel:
            timeout = self.timeout
        # Convert from Gevent-style timeout to threading style
        if timeout is None:
            timeout = -1
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
        """ """
        self._lock.release()

    def _is_owned(self):
        """ """
        return self._lock._is_owned()


class CompositeLock:
    """Class that behaves like a :py:class:`labthings.core.lock.StrictLock`,
    but allows multiple locks to be acquired and released.

    :param locks: List of parent RLock objects
    :type locks: list
    :param timeout: Time in seconds acquisition will wait before raising an exception
    :type timeout: int

    """

    def __init__(self, locks, timeout=-1):
        self.locks = locks
        self.timeout = timeout

    @property
    def _owner(self):
        """ """
        return [lock._owner for lock in self.locks]

    @contextmanager
    def __call__(self, timeout=sentinel, blocking=True):
        result = self.acquire(timeout=timeout, blocking=blocking)
        yield result
        if result:
            self.release()

    def acquire(self, blocking=True, timeout=sentinel):
        """

        :param blocking:  (Default value = True)
        :param timeout:  (Default value = sentinel)

        """
        # If no timeout is given, use object level timeout
        if timeout is sentinel:
            timeout = self.timeout
        # Convert from Gevent-style timeout to threading style
        if timeout is None:
            timeout = -1

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
        """ """
        # If not all child locks are owner by caller
        if not all(owner == current_thread().ident for owner in self._owner):
            raise RuntimeError("cannot release un-acquired lock")
        for lock in self.locks:
            if lock.locked():
                lock.release()

    def _emergency_release(self):
        """ """
        for lock in self.locks:
            if lock.locked() and lock._is_owned():
                lock.release()

    def locked(self):
        """ """
        return any(lock.locked() for lock in self.locks)

    def _is_owned(self):
        """ """
        return all(lock._is_owned() for lock in self.locks)
