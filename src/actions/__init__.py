import importlib
import logging
import pkgutil

from sensor import settings
from sensor.utils import copy_driver_files
from scos_actions.discover import test_actions

logger = logging.getLogger(__name__)
logger.debug("scos-sensor/actions/__init")

copy_driver_files()  # copy driver files before loading plugins

discovered_plugins = {
    name: importlib.import_module(name)
    for finder, name, ispkg in pkgutil.iter_modules()
    if name.startswith("scos_") and name != "scos_actions"
}
logger.debug(discovered_plugins)

# Actions initialized here are made available through the API
registered_actions = {}

if settings.MOCK_SIGAN or settings.RUNNING_TESTS:
    for name, action in test_actions.items():
        logger.debug("test_action: " + name + "=" + str(action))
        registered_actions[name] = action

else:
    for name, module in discovered_plugins.items():
        logger.debug("Looking for actions in " + name + ": " + str(module))
        discover = importlib.import_module(name + ".discover")
        for name, action in discover.actions.items():
            logger.debug("action: " + name + "=" + str(action))
            registered_actions[name] = action

by_name = registered_actions


def get_action_with_summary(action):
    """Given an action, return the string 'action_name - summary'."""
    action_fn = registered_actions[action]
    summary = get_summary(action_fn)
    action_with_summary = action
    if summary:
        action_with_summary += " - {}".format(summary)

    return action_with_summary


def get_summary(action_fn):
    """Extract the first line of the action's description as a summary."""
    description = action_fn.description
    summary = None
    if description:
        summary = description.splitlines()[0]

    return summary


MAX_LENGTH = 50
VALID_ACTIONS = []
CHOICES = []


def init():
    """Allows re-initing VALID_ACTIONS if `registered_actions` is modified."""
    global VALID_ACTIONS
    global CHOICES

    VALID_ACTIONS = sorted(registered_actions.keys())
    for action in VALID_ACTIONS:
        CHOICES.append((action, get_action_with_summary(action)))


init()
