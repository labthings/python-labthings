import threading

import pytest

from labthings.sync import lock

# Fixtures


@pytest.fixture(
    params=["StrictLock", "CompositeLock"],
)
def this_lock(request):
    # Create a fresh lock for each test
    if request.param == "StrictLock":
        return lock.StrictLock()
    elif request.param == "CompositeLock":
        return lock.CompositeLock([lock.StrictLock(), lock.StrictLock()])
    return request.param


# RLock


def test_rlock_acquire(this_lock):
    # Assert no owner
    assert not this_lock.locked()

    # Acquire lock
    assert this_lock.acquire()
    # Assert owner
    assert this_lock._is_owned()

    # Release lock
    this_lock.release()

    # Release lock, assert not held
    assert not this_lock.locked()


def test_rlock_entry(this_lock):
    # Acquire lock
    with this_lock:
        # Assert owner
        assert this_lock._is_owned()

    # Release lock, assert no owner
    assert not this_lock.locked()


def test_rlock_reentry(this_lock):
    # Acquire lock
    with this_lock:
        # Assert owner
        assert this_lock._is_owned()
        # Assert acquirable
        with this_lock as acquired_return:
            assert acquired_return
        # Assert still owned
        assert this_lock._is_owned()

    # Release lock, assert no owner
    assert not this_lock.locked()


def test_rlock_block(this_lock):
    def g():
        this_lock.acquire()

    # Spawn thread
    thread = threading.Thread(target=g)
    thread.start()

    # Assert not owner
    assert not this_lock._is_owned()

    # Assert acquisition fails
    with pytest.raises(lock.LockError):
        this_lock.acquire(blocking=True, timeout=0)

    # Ensure an unheld lock cannot be released
    with pytest.raises(RuntimeError):
        this_lock.release()


def test_rlock_acquire_timeout_pass(this_lock):
    assert not this_lock.locked()

    # Assert acquisition fails using context manager
    with this_lock(timeout=-1) as result:
        assert result is True

    assert not this_lock.locked()


def test_rlock_acquire_timeout_fail(this_lock):
    def g():
        this_lock.acquire()

    # Spawn thread
    thread = threading.Thread(target=g)
    thread.start()

    # Assert not owner
    assert not this_lock._is_owned()

    # Assert acquisition fails using context manager
    with pytest.raises(lock.LockError):
        with this_lock(timeout=0.01):
            pass

class DummyException(Exception):
    pass

def test_rlock_released_after_error_args(this_lock):
    """If an exception occurs in a with block, the lock should release.
    
    NB there are two sets of code that do this - one if arguments are 
    given (i.e. the __call__ method of the lock class) and one without
    arguments (i.e. the __enter__ and __exit__ methods).

    See the following function for the no-arguments version.
    """
    try:
        with this_lock():
            assert this_lock.locked()
            raise DummyException()
    except DummyException:
        pass
    assert not this_lock.locked()

def test_rlock_released_after_error_noargs(this_lock):
    """If an exception occurs in a with block, the lock should release."""
    try:
        with this_lock:
            assert this_lock.locked()
            raise DummyException()
    except DummyException:
        pass
    assert not this_lock.locked()