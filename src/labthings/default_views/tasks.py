from flask import abort

from ..view import View
from ..view.marshalling import marshal_with
from ..schema import TaskSchema

from .. import tasks


class TaskList(View):
    """
    List of all background tasks from the session
    """

    tags = ["tasks"]

    def get(self):
        return TaskSchema(many=True).dump(tasks.tasks())


class TaskView(View):
    """
    Manage a particular background task.

    GET will safely return the current task progress.
    DELETE will terminate the background task, if running.
    """

    tags = ["tasks"]

    def get(self, task_id):
        """
        Show status of a session task

        Includes progress and intermediate data.
        """
        task_dict = tasks.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)

        return TaskSchema().dump(task)

    def delete(self, task_id):
        """
        Terminate a running task.

        If the task is finished, deletes its entry.
        """
        task_dict = tasks.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)

        task.kill(block=True, timeout=3)

        return TaskSchema().dump(task)
