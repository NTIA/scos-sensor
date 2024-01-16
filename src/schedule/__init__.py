import logging

from utils import get_summary
from django.conf import settings

from actions import actions

def get_action_with_summary(action):
    """Given an action, return the string 'action_name - summary'."""
    action_fn = actions[action]
    summary = get_summary(action_fn)
    action_with_summary = action
    if summary:
        action_with_summary += f" - {summary}"

    return action_with_summary


logger = logging.getLogger(__name__)
logger.debug("********** Initializing schedule **********")

