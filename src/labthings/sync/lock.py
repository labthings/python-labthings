from threading import RLock, current_thread

from contextlib import contextmanager
import logging

sentinel = object()


class LockError(RuntimeError):
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
            self.release()
            logging.error(f"Unable to acquire {self} within {timeout} seconds")
            raise LockError("ACQUIRE_ERROR", self)

        return True

    def __enter__(self):
        return self.acquire(blocking=True, timeout=self.timeout)

    def __exit__(self, *args):
        return self.release()

    def release(self):
        # If not all child locks are owner by caller
        for lock in self.locks:
            if lock.locked() and lock._is_owned():
                try:
                    lock.release()
                    logging.debug(f"Released lock {lock}")
                except RuntimeError as e:
                    logging.error(e)

    def locked(self):
        return any(lock.locked() for lock in self.locks)

    def _is_owned(self):
        return all(lock._is_owned() for lock in self.locks)
