import pytest
import labthings.core.tasks as tasks
import time
import logging

#@pytest.fixture
def count(N, dt=0.01):
    for i in range(N):
        time.sleep(dt)
        logging.info(f"Counted to {i}")

def test_logging():
    logging.getLogger().setLevel("INFO")
    task = tasks.taskify(count)(10)
    task.join()
    assert len(task.log) == 10