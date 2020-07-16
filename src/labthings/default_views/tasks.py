from flask import abort
import logging

from ..view import View
from ..view.marshalling import marshal_with
from ..schema import TaskSchema
from ..find import current_thing


class TaskList(View):
    """
    List of all background tasks from the session
    """

    tags = ["tasks"]

    def get(self):
        logging.warning(
            "TaskList is deprecated and will be removed in a future version. Use the Actions list instead."
        )
        return TaskSchema(many=True).dump(current_thing.actions.threads)


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
        logging.warning(
            "TaskView is deprecated and will be removed in a future version. Use the Action view instead."
        )
        task_dict = current_thing.actions.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)

        return TaskSchema().dump(task)

    def delete(self, task_id):
        """
        Terminate a running task.

        If the task is finished, deletes its entry.
        """
        logging.warning(
            "TaskView is deprecated and will be removed in a future version. Use the Action view instead."
        )
        task_dict = current_thing.actions.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)
        task.stop(timeout=5)

        return TaskSchema().dump(task)
