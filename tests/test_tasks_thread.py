from labthings.actions import thread, pool
import threading

import time


def test_task_with_args():
    def task_func(arg, kwarg=False):
        pass

    task_obj = thread.ActionThread(
        target=task_func, args=("String arg",), kwargs={"kwarg": True}
    )
    assert isinstance(task_obj, threading.Thread)
    assert task_obj._target == task_func
    assert task_obj._args == ("String arg",)
    assert task_obj._kwargs == {"kwarg": True}


def test_task_without_args():
    def task_func():
        pass

    task_obj = thread.ActionThread(target=task_func)

    assert isinstance(task_obj, threading.Thread)
    assert task_obj._target == task_func
    assert task_obj._args == ()
    assert task_obj._kwargs == {}


def test_task_start():
    def task_func():
        return "Return value"

    task_obj = thread.ActionThread(target=task_func)

    assert task_obj._status == "pending"
    assert task_obj._return_value is None

    task_obj.start()
    task_obj.join()
    assert task_obj._return_value == "Return value"
    assert task_obj._status == "success"


def test_task_exception():
    exc_to_raise = Exception("Exception message")

    def task_func():
        raise exc_to_raise

    task_obj = thread.ActionThread(target=task_func)
    task_obj.start()
    task_obj.join()

    assert task_obj._status == "error"
    assert task_obj._return_value == str(exc_to_raise)


def test_task_stop():
    def task_func():
        while not pool.current_action().stopped:
            time.sleep(0)

    task_obj = thread.ActionThread(target=task_func)
    task_obj.start()
    task_obj.started.wait()
    assert task_obj._status == "running"
    task_obj.stop()
    task_obj.join()
    assert task_obj._status == "stopped"
    assert task_obj._return_value is None


def test_task_terminate():
    def task_func():
        while True:
            time.sleep(0.5)

    task_obj = thread.ActionThread(target=task_func)
    task_obj.start()
    task_obj.started.wait()
    assert task_obj._status == "running"
    task_obj.terminate()
    task_obj.join()
    assert task_obj._status == "terminated"
    assert task_obj._return_value is None


def test_task_log_list():
    import logging
    import os

    logging.getLogger().setLevel("INFO")

    def task_func():
        logging.warning("Task warning")
        for i in range(10):
            logging.info(f"Counted to {i}")

    task_obj = thread.ActionThread(target=task_func)
    task_obj.start()
    task_obj.started.wait()

    task_obj.join()
    assert task_obj.log[0]["message"] == "Task warning"
    assert task_obj.log[0]["levelname"] == "WARNING"
    assert task_obj.log[0]["filename"] == os.path.basename(__file__)
    assert (
        len(task_obj.log) == 11
    ), "Didn't get the right number of log entries - are INFO entries being logged?"


def test_task_log_without_thread():

    task_log_handler = thread.ThreadLogHandler()

    # Should always return True if not attached to a thread
    assert task_log_handler.check_thread(record=None)


def test_task_log_with_incorrect_thread():

    task_obj = thread.ActionThread(None)
    task_log_handler = thread.ThreadLogHandler(thread=task_obj)

    # Should always return False if called from outside the log handlers thread
    assert task_log_handler.thread == task_obj
    assert not task_log_handler.check_thread(record=None)
