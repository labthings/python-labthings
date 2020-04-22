from labthings.core.tasks import taskify, dictionary

import gevent


def test_docs(thing, thing_client):
    with thing_client as c:
        assert c.get("/docs/swagger").json == thing.spec.to_dict()
        assert c.get("/docs/swagger-ui").status_code == 200


def test_extensions(thing_client):
    with thing_client as c:
        assert c.get("/extensions").json == []


def test_tasks_list(thing_client):
    def task_func():
        pass

    task_obj = taskify(task_func)()

    with thing_client as c:
        response = c.get("/tasks").json
        assert len(response) == 1
        assert response[0].get("id") == str(task_obj.id)


def test_task_representation(thing_client):
    def task_func():
        pass

    task_obj = taskify(task_func)()
    task_id = str(task_obj.id)

    with thing_client as c:
        response = c.get(f"/tasks/{task_id}").json
        assert response


def test_task_representation_missing(thing_client):
    with thing_client as c:
        assert c.get(f"/tasks/missing_id").status_code == 404


def test_task_kill(thing_client):
    def task_func():
        while True:
            gevent.sleep(0)

    task_obj = taskify(task_func)()
    task_id = str(task_obj.id)

    # Wait for task to start
    task_obj.started_event.wait()
    assert task_id in dictionary()

    # Send a DELETE request to terminate the task
    with thing_client as c:
        assert c.delete(f"/tasks/{task_id}").status_code == 200
    # Test task was terminated
    assert task_obj.state.get("status") == "terminated"


def test_task_kill_missing(thing_client):
    with thing_client as c:
        assert c.delete(f"/tasks/missing_id").status_code == 404
