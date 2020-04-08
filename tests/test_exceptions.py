from labthings.core import exceptions
import pytest


def test_lockerror_valid_code():
    from threading import Lock

    lock = Lock()

    assert exceptions.LockError("ACQUIRE_ERROR", lock)
    assert (
        str(exceptions.LockError("ACQUIRE_ERROR", lock))
        == f"ACQUIRE_ERROR: LOCK {lock}: Unable to acquire. Lock in use by another thread."
    )


def test_lockerror_invalid_code():
    from threading import Lock

    lock = Lock()

    assert exceptions.LockError("INVALID_ERROR", lock)
    assert (
        str(exceptions.LockError("INVALID_ERROR", lock))
        == f"INVALID_ERROR: LOCK {lock}: Unknown error."
    )
