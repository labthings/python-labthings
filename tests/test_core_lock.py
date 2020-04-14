from labthings.core import lock
import pytest
from gevent.hub import getcurrent

# Fixtures


@pytest.fixture(
    params=[
        lock.StrictLock(),
        lock.CompositeLock([lock.StrictLock(), lock.StrictLock()]),
    ],
    ids=["StrictLock", "CompositeLock"],
)
def this_lock(request):
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
    from labthings.core.exceptions import LockError

    # Acquire lock
    assert this_lock.acquire()

    # Override owner to force acquisition failure
    this_lock._owner = None
    print(this_lock._owner)
    # Assert not owner
    assert not this_lock._is_owned()

    # Assert acquisition fails
    with pytest.raises(LockError):
        this_lock.acquire(blocking=True, timeout=0.01)

    # Ensure an unheld lock cannot be released
    with pytest.raises(RuntimeError):
        this_lock.release()

    # Force ownership
    this_lock._owner = getcurrent()

    # Release lock
    this_lock.release()

    # Release lock, assert no owner
    assert not this_lock._is_owned()
