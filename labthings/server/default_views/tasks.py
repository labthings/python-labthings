from flask import abort

from ..decorators import marshal_with, Tag
from ..view import View
from ..schema import TaskSchema

from ...core import tasks


@Tag("tasks")
class TaskList(View):
    @marshal_with(TaskSchema(many=True))
    def get(self):
        """List of all session tasks"""
        return tasks.tasks()


@Tag(["properties", "tasks"])
class TaskView(View):
    """
    Manage a particular background task.

    GET will safely return the current task progress.
    DELETE will terminate the background task, if running.
    """

    @marshal_with(TaskSchema())
    def get(self, task_id):
        """
        Show status of a session task

        Includes progress and intermediate data.
        """
        task_dict = tasks.dictionary()

        if not task_id in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)

        return task

    @marshal_with(TaskSchema())
    def delete(self, task_id):
        """
        Terminate a running task.

        If the task is finished, deletes its entry.
        """
        task_dict = tasks.dictionary()

        if not task_id in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)

        task.kill(block=True, timeout=3)

        return task
