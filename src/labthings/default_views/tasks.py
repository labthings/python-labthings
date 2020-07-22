from flask import abort
import logging

from ..views import View
from ..views.marshalling import marshal_with
from ..views.args import use_args
from ..schema import TaskSchema
from ..find import current_labthing
from .. import fields


class TaskList(View):
    """List of all background actions from the session"""

    logging.warning(
        "TaskList is deprecated and will be removed in a future version. Use the Actions list instead."
    )

    def get(self):
        return TaskSchema(many=True).dump(current_labthing().actions.threads)


class TaskView(View):
    """Manage a particular background task.
    
    GET will safely return the current task progress.
    DELETE will terminate the background task, if running.
    """

    logging.warning(
        "TaskList is deprecated and will be removed in a future version. Use the Actions list instead."
    )

    def get(self, task_id):
        """Show status of a session task
        
        Includes progress and intermediate data.

        :param task_id: 

        """
        task_dict = current_labthing().actions.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)

        return TaskSchema().dump(task)

    @use_args({"timeout": fields.Int()})
    def delete(self, args, task_id):
        """Terminate a running task.
        
        If the task is finished, deletes its entry.

        :param task_id: 

        """
        timeout = args.get("timeout", None)
        task_dict = current_labthing().actions.to_dict()

        if task_id not in task_dict:
            return abort(404)  # 404 Not Found

        task = task_dict.get(task_id)
        task.stop(timeout=timeout)

        return TaskSchema().dump(task)
