from flask import abort, url_for

from ..decorators import marshal_with, Tag
from ..view import View
from ..schema import TaskSchema

from ...core import tasks


@Tag("tasks")
class TaskList(View):
    @marshal_with(TaskSchema(many=True))
    def get(self):
        """
        List of all session tasks
        """
        return tasks.tasks()


@Tag(["properties", "tasks"])
class TaskView(View):
    @marshal_with(TaskSchema())
    def get(self, id):
        """
        Show status of a session task

        Includes progress and intermediate data.
        """
        try:
            task = tasks.dict()[id]
        except KeyError:
            return abort(404)  # 404 Not Found

        return task

    @marshal_with(TaskSchema())
    def delete(self, id):
        """
        Terminate a running task.

        If the task is finished, deletes its entry.
        """
        try:
            task = tasks.dict()[id]
        except KeyError:
            return abort(404)  # 404 Not Found

        task.terminate()

        return task
