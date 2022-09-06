from scos_actions.capabilities import capabilities
import actions

import logging

logger = logging.getLogger(__name__)

logger.debug("************** scos-sensor/capabilities/__init__.py *******************")

sensor_capabilities = capabilities
actions_by_name = actions.registered_actions
