from labthings.core import tasks

import gevent


def test_docs(thing, thing_client, schemas_path):

    with thing_client as c:
        json_out = c.get("/docs/swagger").json
        assert "openapi" in json_out
        assert "paths" in json_out
        assert "info" in json_out
        assert c.get("/docs/swagger-ui").status_code == 200


def test_extensions(thing_client):
    with thing_client as c:
        assert c.get("/extensions").json == []


def test_tasks_list(thing_client):
    def task_func():
        pass

    task_obj = tasks.taskify(task_func)()

    with thing_client as c:
        response = c.get("/tasks").json
        ids = [task.get("id") for task in response]
        assert str(task_obj.id) in ids


def test_task_representation(thing_client):
    def task_func():
        pass

    task_obj = tasks.taskify(task_func)()
    task_id = str(task_obj.id)

    with thing_client as c:
        response = c.get(f"/tasks/{task_id}").json
        assert response


def test_task_representation_missing(thing_client):
    with thing_client as c:
        assert c.get("/tasks/missing_id").status_code == 404


def test_task_kill(thing_client):
    def task_func():
        while True:
            gevent.sleep(0)

    task_obj = tasks.taskify(task_func)()
    task_id = str(task_obj.id)

    # Wait for task to start
    task_obj.started_event.wait()
    assert task_id in tasks.to_dict()

    # Send a DELETE request to terminate the task
    with thing_client as c:
        assert c.delete(f"/tasks/{task_id}").status_code == 200
    # Test task was terminated
    assert task_obj.state.get("status") == "terminated"


def test_task_kill_missing(thing_client):
    with thing_client as c:
        assert c.delete("/tasks/missing_id").status_code == 404
