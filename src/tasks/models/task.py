"""Defines a task.

See https://hg.python.org/cpython/file/3.5/Lib/sched.py#l42.

"""

from collections import namedtuple

import actions

attributes = ("time", "priority", "action", "schedule_entry_name", "task_id")
TaskTuple = namedtuple("Task", attributes)


class Task(TaskTuple):
    @property
    def action_caller(self):
        """Action function with curried keyword arguments"""
        action_caller = actions.by_name[self.action]
        return action_caller

    def __eq__(s, o):
        return (s.time, s.priority) == (o.time, o.priority)

    def __lt__(s, o):
        return (s.time, s.priority) < (o.time, o.priority)

    def __le__(s, o):
        return (s.time, s.priority) <= (o.time, o.priority)

    def __gt__(s, o):
        return (s.time, s.priority) > (o.time, o.priority)

    def __ge__(s, o):
        return (s.time, s.priority) >= (o.time, o.priority)
