from scos_actions.capabilities import capabilities
from scos_actions.actions.interfaces.signals import register_action
from utils.action_registrar import registered_actions


import logging

logger = logging.getLogger(__name__)
logger.debug("****s********** scos-sensor/capabilities/__init__.py *******************")
actions_by_name = registered_actions
sensor_capabilities = capabilities
