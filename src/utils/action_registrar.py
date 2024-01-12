import logging
from collections import OrderedDict

from scos_actions.signals import register_action

logger = logging.getLogger(__name__)

logger.debug("Creating Actions dictionary")
registered_actions = OrderedDict()


def add_action_handler(sender, **kwargs):
    action = kwargs["action"]
    logger.debug(f"adding action {action}")
    registered_actions[action.name] = action

logger.debug("Connected register action handler")
register_action.connect(add_action_handler)
