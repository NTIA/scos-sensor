"""Defines the task priority queue used by the scheduler.

See https://hg.python.org/cpython/file/3.5/Lib/sched.py.

"""

import heapq

from .models import Task


class TaskQueue(list):
    """A priority queue for tasks."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        heapq.heapify(self)

    def enter(self, time, priority, action, schedule_entry_name, task_id):
        """Enter an task into the queue and return the unique task id."""
        evt = Task(time, priority, action, schedule_entry_name, task_id)
        heapq.heappush(self, evt)

    def to_list(self):
        """Retun a list of up upcoming tasks in priority queue order."""
        tasks = self.copy()
        # sort method pulled from stdlib sched.py ensures same ordering as pop
        return list(map(heapq.heappop, [tasks] * len(tasks)))

    def cancel(self, task):
        self.remove(task)
        heapq.heapify(self)

    def pop(self):
        return heapq.heappop(self)

    @property
    def next_task(self):
        return self[0]

    def __getitem__(self, item):
        return self.to_list()[item]

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, list(self))
