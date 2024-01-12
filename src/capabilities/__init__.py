import logging

from scos_actions.capabilities import capabilities
from actions import actions


logger = logging.getLogger(__name__)
logger.debug("********** Initializing capabilities **********")
actions_by_name = actions
sensor_capabilities = capabilities
