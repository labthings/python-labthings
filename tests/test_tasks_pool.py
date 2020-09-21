import threading

from labthings import actions


def test_spawn_without_context(task_pool):
    def task_func():
        pass

    task_obj = task_pool.spawn("task_func", task_func)
    assert isinstance(task_obj, threading.Thread)


def test_spawn_with_context(app_ctx, task_pool):
    def task_func():
        pass

    with app_ctx.test_request_context():
        task_obj = task_pool.spawn("task_func", task_func)
        assert isinstance(task_obj, threading.Thread)


def test_update_task_data(task_pool):
    def task_func():
        actions.update_action_data({"key": "value"})

    task_obj = task_pool.spawn("task_func", task_func)
    task_obj.join()
    assert task_obj.data == {"key": "value"}


def test_update_task_data_main_thread():
    # Should do nothing
    actions.update_action_data({"key": "value"})


def test_update_task_progress(task_pool):
    def task_func():
        actions.update_action_progress(100)

    task_obj = task_pool.spawn("task_func", task_func)
    task_obj.join()
    assert task_obj.progress == 100


def test_update_task_progress_main_thread():
    # Should do nothing
    actions.update_action_progress(100)


def test_tasks_list(task_pool):
    assert all(isinstance(task_obj, threading.Thread) for task_obj in task_pool.threads)


def test_tasks_dict(task_pool):
    assert all(
        isinstance(task_obj, threading.Thread)
        for task_obj in task_pool.to_dict().values()
    )

    assert all(k == str(t.id) for k, t in task_pool.to_dict().items())


def test_discard_id(task_pool):
    def task_func():
        pass

    task_obj = task_pool.spawn("task_func", task_func)
    assert str(task_obj.id) in task_pool.to_dict()
    task_obj.join()

    task_pool.discard_id(task_obj.id)
    assert not str(task_obj.id) in task_pool.to_dict()


def test_cleanup_task(task_pool):
    import time

    def task_func():
        pass

    # Make sure at least 1 actions is around
    task_pool.spawn("task_func", task_func)

    # Wait for all actions to finish
    task_pool.join()

    assert len(task_pool.threads) > 0
    task_pool.cleanup()
    assert len(task_pool.threads) == 0
