import logging

from initialization import action_loader, capabilities_loader

logger = logging.getLogger(__name__)
logger.debug("********** Initializing capabilities **********")
actions_by_name = action_loader.actions
logger.debug(f"ActionLoader has {len(action_loader.actions)} actions")
sensor_capabilities = capabilities_loader.capabilities
