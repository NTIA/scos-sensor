import logging

from utils import get_summary
from utils.action_registrar import registered_actions


def get_action_with_summary(action):
    """Given an action, return the string 'action_name - summary'."""
    action_fn = registered_actions[action]
    summary = get_summary(action_fn)
    action_with_summary = action
    if summary:
        action_with_summary += " - {}".format(summary)

    return action_with_summary


logger = logging.getLogger(__name__)
logger.debug("********** Initializing schedule **********")
actions = registered_actions
