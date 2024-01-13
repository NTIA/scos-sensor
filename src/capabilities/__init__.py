import logging

from scos_actions.capabilities import capabilities
from django.conf import settings


logger = logging.getLogger(__name__)
logger.debug("********** Initializing capabilities **********")
actions_by_name = settings.ACTIONS
sensor_capabilities = capabilities
