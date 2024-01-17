import hashlib
import json
import logging

from initialization import action_loader

from django.conf import settings
from initialization import action_loader
from initialization import capabilities_loader



logger = logging.getLogger(__name__)
logger.debug("********** Initializing capabilities **********")
actions_by_name = action_loader.actions
logger.debug(f"ActionLoader has {len(action_loader.actions)} actions")


logger.debug("Capabilites connected to register_action")

sensor_capabilities = capabilities_loader.capabilities
