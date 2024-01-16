import logging

from django.conf import settings
from actions import actions


logger = logging.getLogger(__name__)
logger.debug("********** Initializing capabilities **********")
actions_by_name = actions
sensor_capabilities = settings.CAPABILITIES
