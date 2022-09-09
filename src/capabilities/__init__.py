import logging

from scos_actions.actions.interfaces.signals import register_action
from scos_actions.capabilities import capabilities

from utils.action_registrar import registered_actions

logger = logging.getLogger(__name__)
logger.debug("********** Initializing capabilities **********")
actions_by_name = registered_actions
sensor_capabilities = capabilities
