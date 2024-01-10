import logging

from utils.component_registrar import registered_actions

logger = logging.getLogger(__name__)
logger.debug("********** Initializing tasks **********")
actions = registered_actions
