from . import acquire700c
from . import logger
from . import mock_acquire


by_name = {
    "acquire700c": acquire700c.LTE700cAcquisition(),
    "logger": logger.Logger(),
    "mock_acquire": mock_acquire.TestAcquisition()
}


def get_action_with_summary(action):
    action_fn = by_name[action]
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
VALID_ACTIONS = sorted(by_name.keys())
CHOICES = []
for action in VALID_ACTIONS:
    CHOICES.append((action, get_action_with_summary(action)))
