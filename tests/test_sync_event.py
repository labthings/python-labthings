import threading
import time

from labthings.sync import event


def test_clientevent_init():
    assert event.ClientEvent()


def test_clientevent_greenlet_wait():
    e = event.ClientEvent()

    def g():
        # Wait for e.set()
        return e.wait()

    # Spawn thread
    thread = threading.Thread(target=g)
    thread.start()
    # Wait for e to notice greenlet is waiting for it
    while e.events == {}:
        time.sleep(0)

    # Assert greenlet is in the list of threads waiting for e
    assert thread.ident in e.events

    # Set e from main thread
    # Should cause greenlet to exit due to wait ending as event is set
    e.set()
    # Wait for greenlet to finish
    thread.join()
    ## Ensure greenlet successfully waited without timing out
    # assert greenlet.value == True


def test_clientevent_greenlet_wait_timeout():
    e = event.ClientEvent()

    def g():
        # Wait for e.set(), but timeout immediately
        result = e.wait(timeout=0)
        return result

    # Spawn thread
    thread = threading.Thread(target=g)
    thread.start()
    # Wait for greenlet to finish without ever setting e
    thread.join()


def test_clientevent_greenlet_wait_clear():
    e = event.ClientEvent()

    def g():
        # Wait for e.set()
        e.wait()
        # Clear e for this greenlet
        # This informs e that the greenlet is alive
        # and waiting for e to be set again
        return e.clear()

    # Spawn thread
    thread = threading.Thread(target=g)
    thread.start()
    # Wait for e to notice greenlet is waiting for it
    while e.events == {}:
        time.sleep(0)

    # Set e from main thread
    e.set()
    # Wait for greenlet to finish
    thread.join()


def test_clientevent_greenlet_wait_clear_wrong_greenlet():
    e = event.ClientEvent()

    def g():
        return e.wait()

    # Spawn thread
    thread = threading.Thread(target=g)
    thread.start()
    # Wait for e to notice greenlet is waiting for it
    while e.events == {}:
        time.sleep(0)

    # Set e from main thread
    e.set()
    # Wait for greenlet to finish
    thread.join()
    # Try to clear() e from main thread
    # Should return False since main thread isn't registered as waiting for e
    assert e.clear() == False


def test_clientevent_drop_client():
    e = event.ClientEvent()

    def g():
        # Wait for e.set()
        e.wait()
        # Exit without clearing

    # Spawn thread
    thread = threading.Thread(target=g)
    thread.start()
    # Wait for e to notice greenlet is waiting for it
    while e.events == {}:
        time.sleep(0)

    # Set e from main thread, causing the greenlet to exit
    e.set()
    # Wait for greenlet to finish
    thread.join()
    # Set e from main thread again, with immediate timeout
    # This means that if the client greenlet hasn't cleared the event
    # within 0 seconds, it will be assumed to have exited and dropped
    # from the internal event list
    e.set(timeout=0)

    # Assert that the exited greenlet was dropped from e
    assert thread.ident not in e.events
