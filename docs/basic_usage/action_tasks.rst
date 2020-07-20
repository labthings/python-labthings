Action tasks
============

Many actions in your LabThing may perform tasks that take a long time (compared to the expected response time of a web request). For example, if you were to implement a timelapse action, this inherently runs over a long time.

This introduces a couple of problems. Firstly, a request that triggers a long function will, by default, block the Python interpreter for the duration of the function. This usually causes the connection to timeout, and the response will never be revieved.

Tasks are introduced to manage long-running functions in a way that does not block HTTP requests. Any API Action will automatically run as a task.

Internally, the :class:`labthings.LabThing` object stores a list of all requested actions, and their states. This state stores the running status of the action (if itis idle, running, error, or success), information about the start and end times, a unique task ID, and, upon completion, the return value of the long-running function. 

By using  tasks, a function can be started in the background, and it's return value fetched at a later time once it has reported success. If a long-running action is started by some client, it should note the ID returned in the action state JSON, and use this to periodically check on the status of that particular action. 

API routes have been created to allow checking the state of all actions (GET ``/actions``), a particular task by ID (GET ``/actions/<action_id>``), and terminating or removing individual tasks (DELETE ``/actions/<action_id>``).

All Actions will return a serialized representation of the task, when your POST request returns. If the task completes within a default timeout period (usually 1 second) then the completed Action representation will be returned. If the task is still running after this timeout period, the "in-progress" Action representation will be returned. The final output value can then be retrieved at a later time.

Most users will not need to create instances of this class. Instead, they will be created automatically when a function is started by an API Action view.

.. autoclass:: labthings.tasks.TaskThread
   :members:


Accessing the current task
++++++++++++++++++++++++++

A function running inside a :class:`labthings.tasks.TaskThread` is able to access the instance it is running in using the :meth:`labthings.current_task` function. This allows the state of the Action to be modified freely.

.. autofunction:: labthings.current_task
   :noindex:


Updating task progress
++++++++++++++++++++++

Some client applications may be able to display progress bars showing the progress of an action. Implementing progress updates in your actions is made easy with the :py:meth:`labthings.update_task_progress` function. This function takes a single argument, which is the action progress as an integer percent (0 - 100).

If your long running function was started within a background task, this function will update the state of the corresponding action object. If your function is called outside of a long-running task (e.g. by some internal code, not the web API), then this function will silently do nothing.

.. autofunction:: labthings.update_task_progress
   :noindex: