"""Defines a task.

See https://hg.python.org/cpython/file/3.5/Lib/sched.py#l42.

"""

from collections import namedtuple


attributes = (
    "time",
    "priority",
    "action_name",
    "action_parameters",
    "schedule_entry_id",
    "task_id"
)
TaskTuple = namedtuple("Event", attributes)


class Task(TaskTuple):
    @property
    def action(self):
        """Action function with curried keyword arguments"""
        from commsensor import actions

        action = actions.getbyname(self.action_name)
        action.set_properties(self.action_parameters)
        return action

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
