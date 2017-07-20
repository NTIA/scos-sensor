"""Defines actions that a user can request the sensor perform.

Actions are callback functions that the scheduler calls at an event's
designated time. An event described in JSON should use the name of the action
function as a string, and the Event type handles mapping the function name to
an actual function described in this module.

For example, the follow would map to a call to :func:`logger` with the keyword
argument `msg=hipri`::

    ...
    "action": "logger",
    "action_parameters": {"msg": "hipri"},
    ...

"""

from sensor import settings
from sensor.exceptions import NoSuchActionError
from sensor.logger import logger

from .acquisition import acquire


registered_actions = {
    "logger": logger,
    "acquire": acquire
}


def getbyname(name: str):
    """Return the action associated with `name` or raise AttributeError."""
    try:
        return registered_actions[name]
    except:
        err = "Action {!r} not defined in {}. Available actions are {!r}."
        err = err.format(name, __name__, list(registered_actions.keys()))
        raise NoSuchActionError(err)


def register_test_actions():
    """Enable actions that are only useful for unit testing."""
    from .acquisition import test_acquire

    registered_actions['test_acquire'] = test_acquire


if settings.DEBUG:
    register_test_actions()
