import logging

from utils.action_registrar import registered_actions

logger = logging.getLogger(__name__)
logger.debug("********** Initializing tasks **********")
actions = registered_actions
