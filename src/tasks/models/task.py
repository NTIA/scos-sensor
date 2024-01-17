"""Defines a task.

See https://hg.python.org/cpython/file/3.5/Lib/sched.py#l42.

"""

import logging
from collections import namedtuple

from initialization import action_loader


logger = logging.getLogger(__name__)

logger.debug("*********** scos-sensor/models/task.py ****************")
attributes = ("time", "priority", "action", "schedule_entry_name", "task_id")
TaskTuple = namedtuple("Task", attributes)


class Task(TaskTuple):
    @property
    def action_caller(self):
        """Action function with curried keyword arguments"""
        action_caller = action_loader.actions[self.action]
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
